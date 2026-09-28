#!/usr/bin/env python
"""Pre-commit guard: blocks secrets from being committed.

Scans every STAGED file for well-known credential patterns and refuses the
commit when a live secret is found. Binary files are skipped.

Usage:  python tools/secret_scan.py [--staged]
Exit 0 = clean, Exit 1 = blocked.
"""

from __future__ import annotations

import re
import subprocess
import sys

# Live-secret patterns. Test/regex contexts are handled by ALLOWLIST below.
PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("Google OAuth client secret", re.compile(r"GOCSPX-[A-Za-z0-9_\-]{20,}")),
    ("Google API key", re.compile(r"AIza[0-9A-Za-z_\-]{35}")),
    ("Google refresh/access token", re.compile(r"ya29\.[0-9A-Za-z_\-]{20,}")),
    ("Meta/WhatsApp token", re.compile(r"EAAG[A-Za-z0-9]{20,}")),
    ("Facebook access token", re.compile(r"EAACEdEose0cBA[0-9A-Za-z]{20,}")),
    ("Slack token", re.compile(r"xox[baprs]-[0-9A-Za-z\-]{10,}")),
    ("Stripe live key", re.compile(r"sk_live_[0-9a-zA-Z]{20,}")),
    ("Private key block", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    ("AWS access key id", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("JSON web token", re.compile(r"eyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}")),
]

# Files where these strings are documentation, regexes, or fake test data.
ALLOWLIST = {
    "app/logging/logger.py",      # redaction regex definitions
    "tests/test_phase0.py",       # deliberate fake secrets for redaction tests
    "tools/secret_scan.py",       # this file
    ".env.example",               # documented placeholders
    "readme.md", "prd.md", "rules.md", "design.md",
    "architecture.md", "ai-loop.md", "memory.md", "phases.md",
}

SENSITIVE_SUFFIXES = {".py", ".json", ".txt", ".md", ".env", ".js", ".html", ".css", ".sql", ".yml", ".yaml"}


def staged_files() -> list[str]:
    out = subprocess.run(["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
                         capture_output=True, text=True, check=False)
    return [line for line in out.stdout.splitlines() if line.strip()]


def scan_file(path: str) -> list[tuple[str, str, int]]:
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as handle:
            lines = handle.readlines()
    except OSError:
        return []
    if path in ALLOWLIST:
        return []
    if not any(path.endswith(s) for s in SENSITIVE_SUFFIXES) and "env" not in path.lower():
        return []
    hits: list[tuple[str, str, int]] = []
    for number, line in enumerate(lines, 1):
        for label, pattern in PATTERNS:
            if pattern.search(line):
                hits.append((path, label, number))
    return hits


def main() -> int:
    files = staged_files()
    all_hits: list[tuple[str, str, int]] = []
    for path in files:
        all_hits.extend(scan_file(path))

    if not all_hits:
        print(f"secret_scan: clean ({len(files)} staged file(s) checked)")
        return 0

    print("\nsecret_scan: COMMIT BLOCKED - possible secrets detected\n")
    for path, label, number in all_hits:
        print(f"  {path}:{number}  {label}")
    print("\nDo not commit these. If a file is legitimately safe, add it to")
    print("ALLOWLIST in tools/secret_scan.py with a comment explaining why.\n")
    return 1


if __name__ == "__main__":
    sys.exit(main())