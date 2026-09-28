"""Phase 2 tests: Flask dashboard routes, metrics, controls, and export.

These tests run against a temporary isolated database seeded with the real
workbook so that ``data/outreach.db`` is never modified.
"""

import unittest
from pathlib import Path

from tests.support import IsolatedDatabase


class TestPhase2Dashboard(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.isolated = IsolatedDatabase()
        cls.isolated.__enter__()

        from app.leads.importer import import_leads_from_excel
        from app.leads.repository import LeadRepository
        from app.config import get_settings

        excel_path = Path(__file__).resolve().parent.parent / "data" / "import" / "Lead for web dg.xlsx"
        summary = import_leads_from_excel(excel_path)
        LeadRepository().upsert_many(summary.leads)

        from app.dashboard.server import create_app

        cls.app = create_app()
        cls.app.config["TESTING"] = True
        cls.client = cls.app.test_client()

    @classmethod
    def tearDownClass(cls):
        cls.isolated.__exit__(None, None, None)

    def test_index_page_renders(self):
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        body = res.get_data(as_text=True)
        self.assertIn("D Web Studio", body)
        self.assertIn("metric-total", body)
        self.assertIn("events-stream", body)

    def test_static_assets_load(self):
        for asset in ("/static/app.css", "/static/app.js"):
            res = self.client.get(asset)
            self.assertEqual(res.status_code, 200, f"{asset} should load")
            res.close()

    def test_api_state_metrics(self):
        res = self.client.get("/api/state")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["metrics"]["total"], 95)
        self.assertEqual(data["metrics"]["priority"], 70)
        self.assertEqual(data["metrics"]["completed"], 0)
        self.assertEqual(data["metrics"]["pending"], 95)
        self.assertTrue(data["dry_run"], "Dashboard must report DRY RUN safety mode")
        self.assertEqual(data["mode"], "DRY RUN")
        self.assertIn("gmail", data["connections"])
        self.assertIn("whatsapp", data["connections"])

    def test_api_leads_listing_and_priority_filter(self):
        res = self.client.get("/api/leads")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json()["count"], 95)

        res = self.client.get("/api/leads?priority=true")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json()["count"], 70)

    def test_api_leads_response_is_secret_free(self):
        res = self.client.get("/api/leads")
        body = res.get_data(as_text=True)
        for secret_marker in ("client_secret", "access_token", "token.json", "credentials.json", "refresh_token"):
            self.assertNotIn(secret_marker, body, f"leads API must not expose {secret_marker}")

    def test_api_control_actions(self):
        res = self.client.post("/api/control", json={"action": "start"})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json()["status"], "ok")

        res = self.client.post("/api/control", json={"action": "pause"})
        self.assertEqual(res.status_code, 200)

        res = self.client.post("/api/control", json={"action": "resume"})
        self.assertEqual(res.status_code, 200)

        res = self.client.post("/api/control", json={"action": "stop"})
        self.assertEqual(res.status_code, 200)

        res = self.client.post("/api/control", json={"action": "invalid_action"})
        self.assertEqual(res.status_code, 400)

    def test_api_control_state_transitions(self):
        self.client.post("/api/control", json={"action": "start"})
        state = self.client.get("/api/state").get_json()
        self.assertEqual(state["run_status"], "RUNNING")

        self.client.post("/api/control", json={"action": "pause"})
        state = self.client.get("/api/state").get_json()
        self.assertEqual(state["run_status"], "PAUSED")

        self.client.post("/api/control", json={"action": "stop"})
        state = self.client.get("/api/state").get_json()
        self.assertEqual(state["run_status"], "STOPPED")

    def test_api_events_records_controls(self):
        self.client.post("/api/control", json={"action": "start"})
        res = self.client.get("/api/events?limit=10")
        self.assertEqual(res.status_code, 200)
        events = res.get_json()["events"]
        self.assertGreaterEqual(len(events), 1)
        for event in events:
            self.assertIn(event["icon"], {"✓", "→", "○", "•", "✕", "?"})
            self.assertTrue(event["message"])

    def test_api_whatsapp_config_validation(self):
        """The connect route must reject missing credentials."""
        res = self.client.post("/api/connections/whatsapp/connect", json={"phone_number_id": ""})
        self.assertEqual(res.status_code, 400, "missing credentials must be rejected")
        self.assertIn("hint", res.get_json())

    def test_api_whatsapp_status_is_secret_free(self):
        res = self.client.get("/api/connections/whatsapp")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertNotIn("access_token", data)
        self.assertEqual(data["provider"], "stub")

    def test_whatsapp_token_is_not_persisted_in_plaintext_db(self):
        """The access token must be stored in the OS keyring, not in SQLite."""
        import sqlite3

        from app.config import get_settings
        from app.database.db import get_connection

        get_connection().execute(
            """
            INSERT INTO connections (id, service, provider, status, phone_number_id)
            VALUES ('conn-test', 'whatsapp', 'meta_cloud', 'CONNECTED', '111')
            ON CONFLICT(service) DO UPDATE SET phone_number_id = '111';
            """
        )
        db_file = get_settings().db_path
        conn = sqlite3.connect(str(db_file))
        try:
            rows = conn.execute("SELECT * FROM connections;").fetchall()
            columns = [c[1] for c in conn.execute("PRAGMA table_info(connections);").fetchall()]
        finally:
            conn.close()
        self.assertNotIn("access_token", columns, "connections table must not store raw tokens")
        for row in rows:
            self.assertNotIn("EAAGtesttoken", str(row))

    def test_api_export_returns_xlsx(self):
        res = self.client.get("/api/export")
        self.assertEqual(res.status_code, 200)
        self.assertIn("spreadsheetml", res.headers["Content-Type"])
        res.close()


if __name__ == "__main__":
    unittest.main()