"""Phase 4 tests: WhatsApp provider adapter, credentials, and connection flow.

No test contacts Meta. Network calls are mocked.
"""

import json
import unittest
from unittest import mock

from tests.support import IsolatedDatabase


class TestPhoneNormalization(unittest.TestCase):
    def test_normalization(self):
        from app.integrations.whatsapp.base import WhatsAppProvider

        n = WhatsAppProvider.normalize_phone
        self.assertEqual(n("+91 98765 43210"), "9876543210")
        self.assertEqual(n("919876543210"), "9876543210")
        self.assertEqual(n("9876543210"), "9876543210")
        self.assertIsNone(n("123"))
        self.assertIsNone(n(""))
        self.assertIsNone(n(None))
        self.assertIsNone(n("Not Available"))


class TestStubProvider(unittest.TestCase):
    def test_stub_never_touches_network(self):
        from app.integrations.whatsapp.stub import StubProvider

        provider = StubProvider()
        with mock.patch("requests.post") as post, mock.patch("requests.get") as get:
            result = provider.send_text("9876543210", "Hello there, quick question.")
        post.assert_not_called()
        get.assert_not_called()
        self.assertEqual(result.status.value, "SENT")
        self.assertTrue(result.provider_message_id.startswith("stub-"))

    def test_stub_dry_run(self):
        from app.integrations.whatsapp.stub import StubProvider

        result = StubProvider().send_text("9876543210", "Hello", dry_run=True)
        self.assertEqual(result.status.value, "DRY_RUN")
        self.assertIsNone(result.provider_message_id)

    def test_missing_number_is_not_available(self):
        from app.integrations.whatsapp.stub import StubProvider

        result = StubProvider().send_text("", "Hello")
        self.assertEqual(result.status.value, "NOT_AVAILABLE")


class TestMetaCloudProvider(unittest.TestCase):
    def _creds(self):
        return {"phone_number_id": "111", "waba_id": "222", "access_token": "EAAGsecret"}

    def test_success_returns_message_id(self):
        from app.integrations.whatsapp.meta_cloud import MetaCloudProvider

        with mock.patch("app.integrations.whatsapp.meta_cloud.load_whatsapp_credentials",
                        return_value=self._creds()):
            with mock.patch("app.integrations.whatsapp.meta_cloud.requests.post") as post:
                post.return_value.status_code = 200
                post.return_value.json.return_value = {
                    "messaging_product": "whatsapp",
                    "messages": [{"id": "wamid.ABC123"}],
                }
                result = MetaCloudProvider().send_text("9876543210", "Hello")
        self.assertEqual(result.status.value, "SENT")
        self.assertEqual(result.provider_message_id, "wamid.ABC123")

    def test_success_without_message_id_is_UNKNOWN_not_SENT(self):
        from app.integrations.whatsapp.meta_cloud import MetaCloudProvider

        with mock.patch("app.integrations.whatsapp.meta_cloud.load_whatsapp_credentials",
                        return_value=self._creds()):
            with mock.patch("app.integrations.whatsapp.meta_cloud.requests.post") as post:
                post.return_value.status_code = 200
                post.return_value.json.return_value = {"ok": True}
                result = MetaCloudProvider().send_text("9876543210", "Hello")
        self.assertEqual(result.status.value, "UNKNOWN")
        self.assertFalse(result.confirmed)

    def test_unreachable_number_is_UNKNOWN(self):
        from app.integrations.whatsapp.meta_cloud import MetaCloudProvider

        with mock.patch("app.integrations.whatsapp.meta_cloud.load_whatsapp_credentials",
                        return_value=self._creds()):
            with mock.patch("app.integrations.whatsapp.meta_cloud.requests.post") as post:
                post.return_value.status_code = 400
                post.return_value.json.return_value = {
                    "error": {"code": 131047, "message": "Re-engagement message"}
                }
                result = MetaCloudProvider().send_text("9876543210", "Hello")
        self.assertEqual(result.status.value, "UNKNOWN")

    def test_network_error_is_UNKNOWN(self):
        import requests

        from app.integrations.whatsapp.meta_cloud import MetaCloudProvider

        with mock.patch("app.integrations.whatsapp.meta_cloud.load_whatsapp_credentials",
                        return_value=self._creds()):
            with mock.patch("app.integrations.whatsapp.meta_cloud.requests.post",
                            side_effect=requests.ConnectionError("boom")):
                result = MetaCloudProvider().send_text("9876543210", "Hello")
        self.assertEqual(result.status.value, "UNKNOWN")

    def test_missing_credentials_never_reports_sent(self):
        from app.integrations.whatsapp.meta_cloud import MetaCloudProvider

        with mock.patch("app.integrations.whatsapp.meta_cloud.load_whatsapp_credentials",
                        return_value=None):
            result = MetaCloudProvider().send_text("9876543210", "Hello")
        self.assertEqual(result.status.value, "UNKNOWN")
        self.assertFalse(result.confirmed)


class TestCredentialStorage(unittest.TestCase):
    def test_token_never_lands_in_database(self):
        self.isolated = IsolatedDatabase()
        self.isolated.__enter__()
        try:
            from app.database.db import get_connection
            from app.integrations.whatsapp import service

            with mock.patch("app.integrations.whatsapp.credentials._keyring", return_value=None):
                with mock.patch("app.integrations.whatsapp.service.test_whatsapp_connection") as test:
                    from app.integrations.whatsapp.base import DeliveryResult, DeliveryStatus
                    test.return_value = DeliveryResult(
                        status=DeliveryStatus.SENT, provider="meta_cloud", detail="ok"
                    )
                    service.connect_whatsapp("111", "222", "EAAGsupersecret")

            import sqlite3

            from app.config import get_settings
            raw = sqlite3.connect(str(get_settings().db_path))
            try:
                cols = [c[1] for c in raw.execute("PRAGMA table_info(connections);").fetchall()]
                rows = raw.execute("SELECT * FROM connections;").fetchall()
            finally:
                raw.close()
            self.assertNotIn("access_token", cols)
            self.assertNotIn("EAAGsupersecret", str(rows))
        finally:
            self.isolated.__exit__(None, None, None)

    def test_connection_info_masks_token(self):
        """With the Meta provider selected, the token must appear only masked."""
        self.isolated = IsolatedDatabase({"WHATSAPP_PROVIDER": "meta_cloud"})
        self.isolated.__enter__()
        try:
            from app.integrations.whatsapp import service

            with mock.patch("app.integrations.whatsapp.credentials._keyring", return_value=None):
                with mock.patch("app.integrations.whatsapp.service.test_whatsapp_connection") as test:
                    from app.integrations.whatsapp.base import DeliveryResult, DeliveryStatus
                    test.return_value = DeliveryResult(
                        status=DeliveryStatus.SENT, provider="meta_cloud", detail="ok"
                    )
                    service.connect_whatsapp("111", "222", "EAAGsupersecrettoken")
                info = service.connection_info().to_dict()

            self.assertEqual(info["provider"], "meta_cloud")
            self.assertTrue(info["token_present"])
            self.assertNotIn("EAAGsupersecrettoken", json.dumps(info),
                             "raw token must never leave the process")
            self.assertTrue(info["token_hint"].startswith("*"), "token must be masked")
            self.assertTrue(info["token_hint"].endswith("oken"))
        finally:
            self.isolated.__exit__(None, None, None)


class TestWhatsAppServiceSend(unittest.TestCase):
    def setUp(self):
        self.isolated = IsolatedDatabase()
        self.isolated.__enter__()
        from app.database.db import get_connection

        self.lead_id = f"lead-{self._testMethodName}"
        get_connection().execute(
            "INSERT INTO leads (id, identity_key, name, phone, is_priority) "
            "VALUES (?, ?, 'T', '9000000000', 1);",
            (self.lead_id, f"phone:{self.lead_id}"),
        )

    def tearDown(self):
        self.isolated.__exit__(None, None, None)

    def test_send_is_recorded(self):
        from app.database.db import get_connection
        from app.integrations.whatsapp import service

        result = service.send_whatsapp_message(
            lead_id=self.lead_id, to="9000000000", body="Hello", dry_run=False
        )
        self.assertEqual(result.status.value, "SENT")
        row = get_connection().execute(
            "SELECT status, channel, provider FROM outreach WHERE lead_id = ?;",
            (self.lead_id,),
        ).fetchone()
        self.assertEqual(row["channel"], "whatsapp")
        self.assertEqual(row["status"], "SENT")

    def test_duplicate_is_prevented(self):
        from app.database.db import get_connection
        from app.integrations.whatsapp import service

        get_connection().execute(
            "INSERT INTO outreach (id, lead_id, channel, status, provider) "
            "VALUES ('o1', ?, 'whatsapp', 'SENT', 'stub');", (self.lead_id,))
        with mock.patch("app.integrations.whatsapp.factory.get_provider") as prov:
            result = service.send_whatsapp_message(
                lead_id=self.lead_id, to="9000000000", body="Hello again", dry_run=False)
        prov.assert_not_called()
        self.assertIn("SKIPPED_DUPLICATE", result.detail)


class TestWhatsAppRoutes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.isolated = IsolatedDatabase()
        cls.isolated.__enter__()
        from app.dashboard.server import create_app

        cls.app = create_app()
        cls.app.config["TESTING"] = True
        cls.client = cls.app.test_client()

    @classmethod
    def tearDownClass(cls):
        cls.isolated.__exit__(None, None, None)

    def test_stub_provider_cannot_falsely_report_connected(self):
        """Saving credentials while WHATSAPP_PROVIDER=stub must not claim CONNECTED."""
        self.isolated = IsolatedDatabase()
        self.isolated.__enter__()
        try:
            from app.integrations.whatsapp import service

            with mock.patch("app.integrations.whatsapp.credentials._keyring", return_value=None):
                outcome = service.connect_whatsapp("111", "222", "EAAGsometoken")
            result = outcome["result"]
            self.assertEqual(result.status.value, "UNKNOWN")
            self.assertNotEqual(result.status.value, "SENT")
            self.assertIn("stub", result.detail.lower())
            self.assertIn("WHATSAPP_PROVIDER=meta_cloud", result.detail)
        finally:
            self.isolated.__exit__(None, None, None)

    def test_status_route(self):
        res = self.client.get("/api/connections/whatsapp")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["provider"], "stub")
        self.assertNotIn("access_token", data)

    def test_connect_requires_fields(self):
        res = self.client.post("/api/connections/whatsapp/connect", json={"phone_number_id": ""})
        self.assertEqual(res.status_code, 400)
        self.assertIn("hint", res.get_json())

    def test_connect_never_echoes_token(self):
        with mock.patch("app.integrations.whatsapp.credentials._keyring", return_value=None):
            with mock.patch("app.integrations.whatsapp.service.test_whatsapp_connection") as test:
                from app.integrations.whatsapp.base import DeliveryResult, DeliveryStatus
                test.return_value = DeliveryResult(
                    status=DeliveryStatus.FAILED, provider="meta_cloud", detail="bad token")
                res = self.client.post("/api/connections/whatsapp/connect", json={
                    "phone_number_id": "111", "waba_id": "222", "access_token": "EAAGleaked"})
        self.assertEqual(res.status_code, 200)
        self.assertNotIn("EAAGleaked", res.get_data(as_text=True))
        self.assertFalse(res.get_json()["connected"])

    def test_test_route(self):
        res = self.client.post("/api/connections/whatsapp/test")
        self.assertEqual(res.status_code, 200)
        self.assertIn("status", res.get_json())


if __name__ == "__main__":
    unittest.main()