"""Entry point for the D Web Studio outreach system.

Usage (from the project root, Windows):
    py -3.14 -m app.main             start the application
    py -3.14 -m app.main --check     run startup self-checks and exit
    py -3.14 -m app.main --config    print the safe config summary and exit
    py -3.14 -m app.main --version   print the version and exit

Secrets are never printed: see app/logging/logger.py (redaction) and
Settings.public_summary().
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

PASS, WARN, FAIL = "PASS", "WARN", "FAIL"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="app.main",
        description="D Web Studio - Local Outreach Automation Dashboard",
    )
    parser.add_argument("--check", action="store_true", help="run startup self-checks and exit")
    parser.add_argument("--config", action="store_true", help="print safe configuration summary and exit")
    parser.add_argument("--version", action="store_true", help="print version and exit")
    parser.add_argument("--import-leads", action="store_true", help="import leads from Excel into the database")
    parser.add_argument("--serve", action="store_true", help="start the local dashboard web server")
    return parser


def _git_ignored(project_root: Path, relative: str) -> bool | None:
    """Return True/False if git can answer, else None when git is unavailable."""
    try:
        completed = subprocess.run(
            ["git", "check-ignore", "-q", relative],
            cwd=str(project_root),
            capture_output=True,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return completed.returncode == 0


def run_self_checks(settings) -> list[tuple[str, str, str]]:
    """Phase 0 acceptance checks. Returns (name, level, detail) rows."""
    results: list[tuple[str, str, str]] = []

    try:
        settings.ensure_directories()
        probe = settings.data_dir / ".write_probe"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
        results.append(("local storage writable", PASS, str(settings.data_dir)))
    except OSError as exc:
        results.append(("local storage writable", FAIL, str(exc)))

    results.append(
        (
            "database path ready",
            PASS if settings.db_path.parent.exists() else FAIL,
            str(settings.db_path),
        )
    )

    import_file = settings.lead_import_path
    if import_file.exists():
        results.append(("lead import file found", PASS, import_file.name))
    else:
        results.append(("lead import file found", WARN, f"not found: {import_file}"))

    creds = settings.gmail_credentials_path
    results.append(
        (
            "gmail credentials present",
            PASS if creds.exists() else WARN,
            "credentials/gmail/credentials.json" if creds.exists() else "add credentials.json",
        )
    )

    token = settings.gmail_token_path
    results.append(
        (
            "gmail authorized",
            PASS if token.exists() else WARN,
            "token.json present" if token.exists() else "connect Gmail from the dashboard",
        )
    )

    ignored = _git_ignored(settings.project_root, ".env")
    if ignored is None:
        results.append(("secrets git-ignored", WARN, "git unavailable to verify"))
    else:
        results.append(
            (
                "secrets git-ignored",
                PASS if ignored else FAIL,
                ".env matched by .gitignore" if ignored else ".env is NOT ignored",
            )
        )

    creds_ignored = _git_ignored(settings.project_root, "credentials/gmail/credentials.json")
    if creds_ignored is not None:
        results.append(
            (
                "credentials git-ignored",
                PASS if creds_ignored else FAIL,
                "credentials/ matched by .gitignore" if creds_ignored else "credentials/ is NOT ignored",
            )
        )

    results.append(
        (
            "mode safety",
            PASS,
            settings.mode_label + (" (no message can be sent)" if settings.dry_run else " (real sends enabled)"),
        )
    )
    return results


def _print_check_report(rows: list[tuple[str, str, str]]) -> int:
    width = max(len(name) for name, _, _ in rows)
    icon = {PASS: "[ OK ]", WARN: "[WARN]", FAIL: "[FAIL]"}
    print("\nD WEB STUDIO - STARTUP SELF-CHECKS\n" + "-" * 60)
    for name, level, detail in rows:
        print(f"{icon[level]} {name.ljust(width)}  {detail}")
    failures = [row for row in rows if row[1] == FAIL]
    warnings = [row for row in rows if row[1] == WARN]
    print("-" * 60)
    print(f"{len(rows) - len(failures) - len(warnings)} passed, {len(warnings)} warning(s), {len(failures)} failed")
    return 1 if failures else 0


def main(argv: list[str] | None = None) -> int:
    from app import __version__

    args = build_parser().parse_args(argv)

    if args.version:
        print(f"d-web-studio-outreach {__version__}")
        return 0

    from app.config import ConfigError, get_settings
    from app.logging import configure_logging, get_logger

    try:
        settings = get_settings(refresh=True)
    except ConfigError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 2

    configure_logging(settings.log_level)
    log = get_logger("app.main")
    log.info("D Web Studio Outreach %s starting (mode=%s)", __version__, settings.mode_label)
    for warning in settings.safety_warnings():
        log.warning(warning)

    if args.import_leads:
        from app.database.db import init_database
        from app.leads.importer import import_leads_from_excel
        from app.leads.repository import LeadRepository
        init_database(settings.db_path)
        summary = import_leads_from_excel(settings.lead_import_path)
        repo = LeadRepository()
        inserted = repo.upsert_many(summary.leads)
        print(f"Imported {inserted} leads from {settings.lead_import_path.name}")
        print(f"Total: {summary.unique_leads_imported}, Priority: {summary.priority_count}, Duplicates merged: {summary.duplicates_merged}")
        return 0

    if args.serve:
        from app.database.db import init_database
        from app.dashboard.server import create_app

        init_database(settings.db_path)
        log.info("Starting dashboard on http://%s:%d", settings.dashboard_host, settings.dashboard_port)
        print(f"\n  D Web Studio Dashboard running at http://{settings.dashboard_host}:{settings.dashboard_port}")
        print("  Press Ctrl+C to stop the server.\n")
        # Loopback-only binding: never expose the dashboard on a public interface.
        create_app().run(
            host=settings.dashboard_host,
            port=settings.dashboard_port,
            debug=False,
            use_reloader=False,
            threaded=True,
        )
        return 0

    if args.config:
        print(json.dumps(settings.public_summary(), indent=2))
        return 0

    if args.check:
        return _print_check_report(run_self_checks(settings))

    print(f"D Web Studio Outreach {__version__} - mode: {settings.mode_label}")
    print(f"Database : {settings.db_path}")
    print(f"Logs     : {settings.logs_dir}")
    for warning in settings.safety_warnings():
        print(f"warning  : {warning}")
    print("\nPhase 0 complete: configuration, storage and logging are operational.")
    print("Next: Phase 1 (lead import + SQLite), then Phase 2 (dashboard).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())