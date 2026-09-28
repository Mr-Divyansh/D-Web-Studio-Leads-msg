"""Excel lead importer with headerless detection and deduplication.

Strictly adheres to project requirements:
1. Detects whether row 1 is a lead instead of a header.
2. Maps all 10 columns (A-J), capturing Column H as unverified notes.
3. Automatically sets NOT_AVAILABLE when contact information is missing.
4. Deduplicates against the identity hierarchy.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import openpyxl

from app.leads.identity import build_identity_key, generate_lead_id
from app.leads.normalize import (
    normalize_age,
    normalize_email,
    normalize_gender,
    normalize_name,
    normalize_phone,
    normalize_priority,
    normalize_text_field,
)
from app.logging import get_logger

log = get_logger("app.leads.importer")


@dataclass
class LeadRecord:
    id: str
    identity_key: str
    name: str
    email: str | None
    email_raw: str
    phone: str | None
    phone_raw: str
    is_priority: bool
    gender: str | None
    age: int | None
    city: str | None
    education: str | None
    source: str
    unverified_notes: str | None
    email_status: str
    whatsapp_status: str
    overall_status: str = "PENDING"
    is_opted_out: bool = False

    def to_db_row(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "identity_key": self.identity_key,
            "name": self.name,
            "email": self.email,
            "email_raw": self.email_raw,
            "phone": self.phone,
            "phone_raw": self.phone_raw,
            "is_priority": 1 if self.is_priority else 0,
            "gender": self.gender,
            "age": self.age,
            "city": self.city,
            "education": self.education,
            "source": self.source,
            "unverified_notes": self.unverified_notes,
            "email_status": self.email_status,
            "whatsapp_status": self.whatsapp_status,
            "overall_status": self.overall_status,
            "is_opted_out": 1 if self.is_opted_out else 0,
        }


@dataclass
class ImportSummary:
    file_path: str
    total_rows_read: int = 0
    unique_leads_imported: int = 0
    duplicates_merged: int = 0
    priority_count: int = 0
    email_available: int = 0
    email_not_available: int = 0
    whatsapp_available: int = 0
    whatsapp_not_available: int = 0
    leads: list[LeadRecord] = field(default_factory=list)


def _is_header_row(row_cells: list[Any]) -> bool:
    """Check if the first row is a header rather than a lead."""
    if not row_cells or not any(row_cells):
        return False
    val0 = str(row_cells[0] or "").strip().lower()
    val1 = str(row_cells[1] or "").strip().lower() if len(row_cells) > 1 else ""

    # Clear header signatures
    header_keywords = {"name", "candidate name", "full name", "lead name"}
    if val0 in header_keywords or val1 in {"email", "email address", "mail"}:
        return True

    # If col 1 has an '@' or col 2 has digits, it is clearly data!
    if "@" in val1:
        return False
    if len(row_cells) > 2 and str(row_cells[2] or "").strip().isdigit():
        return False

    return False


def import_leads_from_excel(file_path: Path | str) -> ImportSummary:
    """Read an Excel file and extract normalized, deduplicated lead records."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Lead file does not exist: {path}")

    log.info("Opening Excel workbook: %s", path)
    wb = openpyxl.load_workbook(filename=str(path), read_only=True, data_only=True)
    sheet = wb.active
    if sheet is None:
        wb.close()
        raise ValueError("Workbook does not contain an active sheet")

    summary = ImportSummary(file_path=str(path))
    seen_identities: dict[str, LeadRecord] = {}

    rows_iter = sheet.iter_rows(values_only=True)
    first_row = next(rows_iter, None)
    if first_row is None:
        wb.close()
        return summary

    rows_to_process: list[list[Any]] = []
    if _is_header_row(list(first_row)):
        log.info("Detected header row on row 1 - skipping")
    else:
        log.info("Row 1 detected as a LEAD (headerless workbook) - processing row 1")
        rows_to_process.append(list(first_row))

    for row in rows_iter:
        if row and any(cell is not None and str(cell).strip() for cell in row):
            rows_to_process.append(list(row))

    wb.close()

    summary.total_rows_read = len(rows_to_process)
    log.info("Processing %d total rows from %s", summary.total_rows_read, path.name)

    for row_vals in rows_to_process:
        # Pad row to 10 columns
        padded = list(row_vals) + [None] * max(0, 10 - len(row_vals))

        raw_name = padded[0]
        raw_email = padded[1]
        raw_phone = padded[2]
        raw_priority = padded[3]
        raw_gender = padded[4]
        raw_age = padded[5]
        raw_city = padded[6]
        raw_notes = padded[7]  # Column H (free text / unverified notes)
        raw_edu = padded[8]
        raw_source = padded[9]

        name = normalize_name(raw_name)
        norm_email, email_raw = normalize_email(raw_email)
        norm_phone, phone_raw = normalize_phone(raw_phone)
        is_priority = normalize_priority(raw_priority)
        gender = normalize_gender(raw_gender)
        age = normalize_age(raw_age)
        city = normalize_text_field(raw_city)
        education = normalize_text_field(raw_edu)
        source = str(raw_source or "Apna").strip() or "Apna"
        unverified_notes = normalize_text_field(raw_notes)

        # Status determination
        email_status = "PENDING" if norm_email else "NOT_AVAILABLE"
        whatsapp_status = "PENDING" if norm_phone else "NOT_AVAILABLE"

        ident_key = build_identity_key(norm_email, norm_phone, name)

        if ident_key in seen_identities:
            # Duplicate record encountered
            summary.duplicates_merged += 1
            existing = seen_identities[ident_key]
            # Backfill any missing fields on existing record
            if not existing.email and norm_email:
                existing.email = norm_email
                existing.email_status = "PENDING"
            if not existing.phone and norm_phone:
                existing.phone = norm_phone
                existing.whatsapp_status = "PENDING"
            if not existing.is_priority and is_priority:
                existing.is_priority = True
            if not existing.unverified_notes and unverified_notes:
                existing.unverified_notes = unverified_notes
            continue

        lead = LeadRecord(
            id=generate_lead_id(),
            identity_key=ident_key,
            name=name,
            email=norm_email,
            email_raw=email_raw,
            phone=norm_phone,
            phone_raw=phone_raw,
            is_priority=is_priority,
            gender=gender,
            age=age,
            city=city,
            education=education,
            source=source,
            unverified_notes=unverified_notes,
            email_status=email_status,
            whatsapp_status=whatsapp_status,
        )

        seen_identities[ident_key] = lead
        summary.leads.append(lead)

    summary.unique_leads_imported = len(summary.leads)
    summary.priority_count = sum(1 for l in summary.leads if l.is_priority)
    summary.email_available = sum(1 for l in summary.leads if l.email)
    summary.email_not_available = sum(1 for l in summary.leads if not l.email)
    summary.whatsapp_available = sum(1 for l in summary.leads if l.phone)
    summary.whatsapp_not_available = sum(1 for l in summary.leads if not l.phone)

    log.info(
        "Import summary for %s: %d total rows -> %d unique leads (%d priority, %d dups merged)",
        path.name,
        summary.total_rows_read,
        summary.unique_leads_imported,
        summary.priority_count,
        summary.duplicates_merged,
    )
    return summary