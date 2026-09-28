"""Unit tests for Phase 0: Configuration, Secret Masking, and Logging."""

import logging
import os
import unittest
from pathlib import Path

from app.config.settings import Settings, get_settings, mask
from app.logging.logger import redact


class TestPhase0(unittest.TestCase):
    def test_secret_masking(self):
        self.assertEqual(mask(""), "")
        self.assertEqual(mask(None), "")
        self.assertEqual(mask("1234"), "****")
        self.assertEqual(mask("my_super_secret_token_1234"), "**********************1234")

    def test_log_redaction(self):
        sample = 'client_secret="GOCSPX-abc123XYZ456" access_token=ya29.secretBearerToken'
        scrubbed = redact(sample)
        self.assertNotIn("GOCSPX-abc123XYZ456", scrubbed)
        self.assertNotIn("ya29.secretBearerToken", scrubbed)
        self.assertIn("***REDACTED***", scrubbed)

    def test_settings_load_and_directories(self):
        settings = get_settings(refresh=True)
        self.assertIsInstance(settings, Settings)
        self.assertTrue(settings.dry_run, "DRY_RUN must default to True for safety")
        self.assertEqual(settings.mode_label, "DRY RUN")
        self.assertTrue(settings.data_dir.exists())
        self.assertTrue(settings.logs_dir.exists())
        summary = settings.public_summary()
        self.assertIn("mode", summary)
        self.assertNotIn("client_secret", str(summary))


if __name__ == "__main__":
    unittest.main()