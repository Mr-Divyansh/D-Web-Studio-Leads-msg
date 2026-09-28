"""Unit and integration tests for Phase 1: Database & Excel Importer."""

import shutil
import tempfile
import unittest
from pathlib import Path

from app.database.db import get_connection, init_database
from app.leads.exporter import export_leads_to_excel
from app.leads.importer import import_leads_from_excel
from app.leads.normalize import (
    normalize_age,
    normalize_email,
    normalize_gender,
    normalize_name,
    normalize_phone,
    normalize_priority,
)
from app.leads.repository import LeadRepository


class TestPhase1(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test_outreach.db"
        init_database(self.db_path)
        self.conn = get_connection(self.db_path)
        self.repo = LeadRepository(self.conn)

    def tearDown(self):
        self.conn.close()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_normalizers(self):
        # Name
        self.assertEqual(normalize_name("john doe"), "John Doe")
        self.assertEqual(normalize_name("N. Sharma"), "N. Sharma")
        self.assertEqual(normalize_name("Not Available"), "Unknown")

        # Email
        norm, raw = normalize_email("Test.User@Example.Com")
        self.assertEqual(norm, "test.user@example.com")
        self.assertEqual(raw, "Test.User@Example.Com")
        norm, _ = normalize_email("Not Available")
        self.assertIsNone(norm)

        # Phone
        norm, _ = normalize_phone("+91-9876543210")
        self.assertEqual(norm, "9876543210")
        norm, _ = normalize_phone("9876543210")
        self.assertEqual(norm, "9876543210")
        norm, _ = normalize_phone("123")  # too short
        self.assertIsNone(norm)

        # Priority
        self.assertTrue(normalize_priority("Priority"))
        self.assertTrue(normalize_priority("priority"))
        self.assertFalse(normalize_priority(""))
        self.assertFalse(normalize_priority("Not Available"))

        # Gender & Age
        self.assertEqual(normalize_gender("Male"), "m")
        self.assertEqual(normalize_gender("F"), "f")
        self.assertEqual(normalize_age("28"), 28)
        self.assertIsNone(normalize_age("abc"))

    def test_import_actual_workbook(self):
        excel_path = Path(__file__).resolve().parent.parent / "data" / "import" / "Lead for web dg.xlsx"
        self.assertTrue(excel_path.exists(), f"Excel file missing at {excel_path}")

        summary = import_leads_from_excel(excel_path)

        # Validate against mathematically audited properties:
        # 100 rows total, 5 duplicates merged = 95 unique leads
        # 71 raw priority rows, 1 duplicate priority row merged = 70 unique priority leads
        self.assertEqual(summary.total_rows_read, 100, "Workbook has exactly 100 rows")
        self.assertEqual(summary.unique_leads_imported, 95, "5 duplicates merged -> 95 unique leads")
        self.assertEqual(summary.duplicates_merged, 5)
        self.assertEqual(summary.priority_count, 70, "Exactly 70 unique priority leads after deduplication")
        self.assertEqual(summary.email_available, 86, "86 unique leads have emails")
        self.assertEqual(summary.email_not_available, 9, "9 unique leads have Not Available email")

        # Check Column H unverified notes presence
        notes_count = sum(1 for l in summary.leads if l.unverified_notes)
        self.assertGreater(notes_count, 0, "Column H unverified notes should be populated")

        # Headerless handling: row 1 is a real lead, not a header.
        # Assert structure only - never hardcode real lead PII into version control.
        self.assertEqual(len(summary.leads), 95, "Row 1 must be imported as a lead, not skipped as a header")
        first = summary.leads[0]
        self.assertNotEqual(first.name, "Unknown", "Row 1 lead name must be parsed")
        self.assertTrue(first.email, "Row 1 lead email must be parsed and normalized")
        self.assertRegex(first.email, r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
        self.assertRegex(first.phone or "", r"^\d{10}$", "Phone must normalize to 10 digits")
        self.assertTrue(first.is_priority)
        self.assertIn(first.gender, {"m", "f", None})

    def test_repository_and_export(self):
        excel_path = Path(__file__).resolve().parent.parent / "data" / "import" / "Lead for web dg.xlsx"
        summary = import_leads_from_excel(excel_path)

        inserted = self.repo.upsert_many(summary.leads)
        self.assertEqual(inserted, 95)
        self.assertEqual(self.repo.count_all(), 95)
        self.assertEqual(self.repo.count_priority(), 70)

        counts = self.repo.get_summary_counts()
        self.assertEqual(counts["total"], 95)
        self.assertEqual(counts["priority"], 70)
        self.assertEqual(counts["completed"], 0)
        self.assertEqual(counts["pending"], 95)

        # Fetch priority eligible leads
        eligible_priority = self.repo.get_eligible_leads(priority_only=True)
        self.assertEqual(len(eligible_priority), 70)

        # Update a channel status and verify state progression
        first_lead = eligible_priority[0]
        self.repo.update_channel_status(first_lead["id"], "email", "SENT")
        updated = self.repo.get_by_id(first_lead["id"])
        self.assertEqual(updated["email_status"], "SENT")
        self.assertEqual(updated["overall_status"], "PROCESSING")

        self.repo.update_channel_status(first_lead["id"], "whatsapp", "SENT")
        updated = self.repo.get_by_id(first_lead["id"])
        self.assertEqual(updated["overall_status"], "COMPLETED")

        # Test export
        export_out = Path(self.temp_dir) / "exported_leads.xlsx"
        result_path = export_leads_to_excel(export_out, self.conn)
        self.assertTrue(result_path.exists())
        self.assertGreater(result_path.stat().st_size, 1000)


if __name__ == "__main__":
    unittest.main()