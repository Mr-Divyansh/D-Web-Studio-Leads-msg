"""Excel export utility for leads and their delivery statuses."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import openpyxl
from openpyxl.styles import Font, PatternFill

from app.database.db import get_connection
from app.logging import get_logger

log = get_logger("app.leads.exporter")


def export_leads_to_excel(output_path: Path | str, conn: sqlite3.Connection | None = None) -> Path:
    """Export the current leads table and delivery history to an Excel workbook."""
    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)

    if conn is None:
        conn = get_connection()

    rows = conn.execute("""
        SELECT
            id, name, email, phone, is_priority, gender, age, city, education,
            source, unverified_notes, email_status, whatsapp_status, overall_status,
            is_opted_out, created_at, updated_at
        FROM leads
        ORDER BY is_priority DESC, name ASC;
    """).fetchall()

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Outreach Leads"

    headers = [
        "Lead ID", "Name", "Email", "Phone", "Priority", "Gender", "Age",
        "City", "Education", "Source", "Notes (Unverified)", "Email Status",
        "WhatsApp Status", "Overall Status", "Opted Out", "Imported At", "Updated At"
    ]
    ws.append(headers)

    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="1F2937", end_color="1F2937", fill_type="solid")
    for cell in ws[1]:
        cell.font = header_font
        cell.fill = header_fill

    for r in rows:
        ws.append([
            r["id"],
            r["name"],
            r["email"] or "N/A",
            r["phone"] or "N/A",
            "Yes" if r["is_priority"] else "No",
            r["gender"] or "",
            r["age"] or "",
            r["city"] or "",
            r["education"] or "",
            r["source"] or "",
            r["unverified_notes"] or "",
            r["email_status"],
            r["whatsapp_status"],
            r["overall_status"],
            "Yes" if r["is_opted_out"] else "No",
            r["created_at"],
            r["updated_at"],
        ])

    wb.save(str(out_file))
    log.info("Exported %d leads to %s", len(rows), out_file)
    return out_file