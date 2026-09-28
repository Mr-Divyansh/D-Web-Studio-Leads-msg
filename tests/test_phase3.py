"""Phase 3 tests: Gmail OAuth, message building, sending, and duplicate prevention.

No test performs a real network call or sends a real email.
"""

import base64
import email
import json
import unittest
from pathlib import Path
from unittest import mock

from tests.support import IsolatedDatabase

VALID_BODY = (
    "Hi there,\n\nI am reaching out from D Web Studio about a website project.\n"
    "Would you be open to a quick 10-minute call this week?\n\nBest regards,\nD Web Studio"
)


class TestGmailMessage(unittest.TestCase):
    def test_build_email_produces_valid_rfc2822(self):
        from app.integrations.gmail.message import build_email

        built = build_email(
            to="  Person@Example.COM ",
            subject="Website enquiry",
            body=VALID_BODY,
            sender_name="D Web Studio",
        )
        self.assertEqual(built.to, "person@example.com", "recipient must be lowercased")
        decoded = base64.urlsafe_b64decode(built.raw).decode("utf-8")
        parsed = email.message_from_string(decoded)
        self.assertEqual(parsed["To"], "person@example.com")
        self.assertEqual(parsed["Subject"], "Website enquiry")
        self.assertIn("D Web Studio", parsed["From"])
        self.assertIn("10-minute call", parsed.get_payload())

    def test_invalid_recipients_are_rejected(self):
        from app.integrations.gmail.message import MessageValidationError, validate_recipient

        for bad in ["", "   ", "not-an-email", "a@b", "@example.com", "a b@example.com"]:
            with self.assertRaises(MessageValidationError):
                validate_recipient(bad)

    def test_empty_content_is_rejected(self):
        from app.integrations.gmail.message import MessageValidationError, validate_content

        with self.assertRaises(MessageValidationError):
            validate_content("", VALID_BODY)
        with self.assertRaises(MessageValidationError):
            validate_content("Subject", "   ")
        with self.assertRaises(MessageValidationError):
            validate_content("Subject", "too short")

    def test_hallucinated_personal_claims_are_blocked(self):
        from app.integrations.gmail.message import MessageValidationError, validate_content

        for phrase in [
            "As I mentioned, your website is great.",
            "Like we spoke, let's continue.",
            "Your business looks interesting.",
            "You told me you needed a site.",
        ]:
            with self.assertRaises(MessageValidationError):
                validate_content("Subject", VALID_BODY + "\n" + phrase)

    def test_unfilled_placeholders_are_blocked(self):
        from app.integrations.gmail.message import MessageValidationError, validate_content

        for body in [VALID_BODY + "\n{{name}}", VALID_BODY + "\n<COMPANY>", VALID_BODY + "\nTODO"]:
            with self.assertRaises(MessageValidationError):
                validate_content("Subject", body)


class TestGmailOAuthConfig(unittest.TestCase):
    def test_client_summary_masks_secret(self):
        from app.integrations.gmail import oauth

        summary = oauth.client_summary()
        self.assertTrue(summary["configured"], "credentials.json should be present")
        self.assertIn("apps.googleusercontent.com", summary["client_id"])
        raw_secret = json.loads(
            Path(oauth._credentials_path()).read_text(encoding="utf-8")
        )["installed"]["client_secret"]
        self.assertNotIn(raw_secret, json.dumps(summary), "raw secret must never be returned")
        self.assertTrue(summary["client_secret"].startswith("*"))

    def test_authorization_url_is_google_and_has_state(self):
        from app.integrations.gmail import oauth

        url = oauth.build_authorization_url("teststate123", "http://localhost:8756/oauth2/callback")
        self.assertIn("https://accounts.google.com/o/oauth2/auth", url)
        self.assertIn("client_id=", url)
        self.assertIn("access_type=offline", url)
        self.assertIn("state=teststate123", url)
        self.assertIn("gmail.send", url)

    def test_verify_reports_not_authorized_without_token(self):
        from app.integrations.gmail import oauth

        with mock.patch.object(oauth, "load_credentials", return_value=None):
            status = oauth.verify_connection()
        self.assertFalse(status.authorized)


class TestGmailSending(unittest.TestCase):
    """Each test uses its own lead so deliveries never interfere."""

    def setUp(self):
        self.isolated = IsolatedDatabase()
        self.isolated.__enter__()
        from app.database.db import get_connection

        self.lead_id = f"lead-{self._testMethodName}"
        get_connection().execute(
            "INSERT INTO leads (id, identity_key, name, email, phone, is_priority) "
            "VALUES (?, ?, 'Test Person', ?, '9000000000', 1);",
            (self.lead_id, f"email:{self.lead_id}@example.com", f"{self.lead_id}@example.com"),
        )

    def tearDown(self):
        self.isolated.__exit__(None, None, None)

    def test_dry_run_never_calls_the_api(self):
        from app.integrations.gmail import sender

        with mock.patch.object(sender, "get_service") as svc:
            result = sender.send_email(
                lead_id=self.lead_id, to=f"{self.lead_id}@example.com",
                subject="Website enquiry", body=VALID_BODY, dry_run=True,
            )
            svc.assert_not_called()
        self.assertEqual(result.status, "DRY_RUN")
        self.assertIsNone(result.message_id)

    def test_duplicate_send_is_prevented(self):
        from app.database.db import get_connection
        from app.integrations.gmail import sender

        get_connection().execute(
            "INSERT INTO outreach (id, lead_id, channel, status, provider) "
            "VALUES ('out-x', ?, 'email', 'SENT', 'gmail');",
            (self.lead_id,),
        )
        with mock.patch.object(sender, "get_service") as svc:
            result = sender.send_email(
                lead_id=self.lead_id, to=f"{self.lead_id}@example.com",
                subject="Website enquiry", body=VALID_BODY, dry_run=False,
            )
            svc.assert_not_called()
        self.assertEqual(result.status, "SKIPPED_DUPLICATE")

    def test_validation_failure_is_recorded_and_not_sent(self):
        from app.integrations.gmail import sender

        with mock.patch.object(sender, "get_service") as svc:
            result = sender.send_email(
                lead_id=self.lead_id, to=f"{self.lead_id}@example.com",
                subject="Hi", body="", dry_run=False,
            )
            svc.assert_not_called()
        self.assertEqual(result.status, "FAILED")
        self.assertIn("empty", result.detail.lower())

    def test_successful_send_records_provider_message_id(self):
        from app.database.db import get_connection
        from app.integrations.gmail import sender

        fake_service = mock.MagicMock()
        fake_service.users().messages().send().execute.return_value = {"id": "gmail-msg-123"}
        with mock.patch.object(sender, "get_service", return_value=fake_service):
            result = sender.send_email(
                lead_id=self.lead_id, to=f"{self.lead_id}@example.com",
                subject="Website enquiry", body=VALID_BODY, dry_run=False,
            )
        self.assertEqual(result.status, "SENT")
        self.assertEqual(result.message_id, "gmail-msg-123")
        row = get_connection().execute(
            "SELECT provider_message_id, status FROM outreach WHERE lead_id = ?;",
            (self.lead_id,),
        ).fetchone()
        self.assertEqual(row["provider_message_id"], "gmail-msg-123")
        self.assertEqual(row["status"], "SENT")

    def test_unique_constraint_blocks_second_outreach_row(self):
        """The database is the final backstop against duplicate sends."""
        import sqlite3

        from app.database.db import get_connection

        conn = get_connection()
        # First attempt succeeds.
        conn.execute(
            "INSERT INTO outreach (id, lead_id, channel, status, provider) "
            "VALUES ('out-first', ?, 'email', 'SENT', 'gmail');",
            (self.lead_id,),
        )
        # A second row for the same lead+channel must be impossible.
        with self.assertRaises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO outreach (id, lead_id, channel, status, provider) "
                "VALUES ('out-dup', ?, 'email', 'SENT', 'gmail');",
                (self.lead_id,),
            )
        # A different channel for the same lead is still allowed.
        conn.execute(
            "INSERT INTO outreach (id, lead_id, channel, status, provider) "
            "VALUES ('out-wa', ?, 'whatsapp', 'SENT', 'stub');",
            (self.lead_id,),
        )
        count = conn.execute(
            "SELECT COUNT(*) FROM outreach WHERE lead_id = ?;", (self.lead_id,)
        ).fetchone()[0]
        self.assertEqual(count, 2, "one row per channel is allowed")


class TestGmailRoutes(unittest.TestCase):
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

    def test_gmail_status_route(self):
        res = self.client.get("/api/connections/gmail")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["client"]["configured"])
        self.assertNotIn("GOCSPX", json.dumps(data), "no raw secret in API output")

    def test_connect_route_returns_url(self):
        res = self.client.get("/api/connections/gmail/connect")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("accounts.google.com", data["authorization_url"])

    def test_callback_rejects_bad_state(self):
        res = self.client.get("/oauth2/callback?code=fake&state=not-a-real-state")
        self.assertEqual(res.status_code, 302)
        self.assertIn("bad_state", res.headers["Location"])

    def test_callback_rejects_missing_code(self):
        res = self.client.get("/oauth2/callback")
        self.assertIn("missing_code", res.headers["Location"])

    def test_callback_handles_denied_consent(self):
        res = self.client.get("/oauth2/callback?error=access_denied")
        self.assertIn("denied", res.headers["Location"])

    def test_email_preview_validates_without_sending(self):
        res = self.client.post("/api/email/preview", json={
            "to": "person@example.com", "subject": "Hello", "body": VALID_BODY})
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.get_json()["valid"])

        res = self.client.post("/api/email/preview", json={
            "to": "person@example.com", "subject": "Hello", "body": "As discussed, your site is great."})
        self.assertEqual(res.status_code, 400)
        self.assertFalse(res.get_json()["valid"])

    def test_diagnose_route_reports_registered_redirects(self):
        """The diagnose endpoint must expose the registered URIs and the one we send."""
        res = self.client.get("/api/connections/gmail/diagnose")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("registered_redirect_uris", data)
        self.assertIn("redirect_uri_being_sent", data)
        self.assertTrue(data["redirect_uri_being_sent"].endswith("/oauth2/callback"))
        self.assertNotIn("GOCSPX", res.get_data(as_text=True))

    def test_redirect_host_can_be_forced_to_localhost(self):
        """OAUTH_REDIRECT_HOST must override the Host header so it matches the client."""
        import os

        os.environ["OAUTH_REDIRECT_HOST"] = "localhost"
        from app.config import get_settings

        get_settings(refresh=True)
        try:
            res = self.client.get("/api/connections/gmail/connect")
            self.assertEqual(res.status_code, 200)
            url = res.get_json()["authorization_url"]
            self.assertIn("http%3A%2F%2Flocalhost%3A", url,
                          "forced host must appear in the authorization URL")
        finally:
            os.environ.pop("OAUTH_REDIRECT_HOST", None)
            get_settings(refresh=True)

    def test_disconnect_route(self):
        res = self.client.post("/api/connections/gmail/disconnect")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json()["status"], "disconnected")

    def test_token_never_written_to_database(self):
        from app.config import get_settings
        import sqlite3

        raw = sqlite3.connect(str(get_settings().db_path))
        try:
            columns = [c[1] for c in raw.execute("PRAGMA table_info(connections);").fetchall()]
        finally:
            raw.close()
        self.assertNotIn("access_token", columns)
        self.assertNotIn("client_secret", columns)


if __name__ == "__main__":
    unittest.main()