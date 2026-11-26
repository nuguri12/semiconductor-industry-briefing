import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from briefing.__main__ import main, read_snapshot
from briefing.delivery import DeliveryLedger


def sample():
    return dict(schema_version=1, collected_at="2026-11-26T12:00:00+09:00",
                query="semiconductor", hours=24, rejected=0, limit_reached=False,
                sources={"GDELT": "failed", "MSIT RSS": "ok"}, status="partial",
                source_details={"GDELT": {"count": 0}, "MSIT RSS": {"count": 1}},
                articles=[dict(title="Semiconductor equipment", url="https://example.test/news",
                               source="MSIT", provider="MSIT RSS", observed_at=None,
                               published_at="2026-11-26", published_precision="date", language="ko")])


class SnapshotTests(unittest.TestCase):
    def test_saved_all_source_failure_returns_failure_exit(self):
        payload = sample()
        payload['articles'] = []
        payload['sources'] = {'GDELT': 'failed', 'MSIT RSS': 'failed'}
        payload['source_details'] = {'GDELT': {'count': 0}, 'MSIT RSS': {'count': 0}}
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'failed.json'
            path.write_text(json.dumps(payload), encoding='utf-8')
            result = subprocess.run([sys.executable, '-m', 'briefing', '--input', str(path), '--json'],
                                    capture_output=True)
            self.assertEqual(result.returncode, 1)

    def test_cli_roundtrip_preserves_all_collection_metadata(self):
        payload = sample()
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "sample.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            result = subprocess.run([sys.executable, "-m", "briefing", "--input", str(path),
                                     "--json"], capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout), payload)

    def test_invalid_snapshot_is_rejected(self):
        for field, value in [("schema_version", 99), ("sources", {}), ("status", "ok"),
                             ("rejected", -1), ("collected_at", "yesterday"),
                             ("source_details", []), ("source_details", {"GDELT": {"count": -1}})]:
            payload = sample()
            payload[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                read_snapshot(payload)
        for field, value in [("url", "javascript:bad"), ("provider", "GDELT"),
                             ("published_at", "2026-11-26T00:00:00")]:
            payload = sample()
            payload["articles"][0][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                read_snapshot(payload)
        payload = sample()
        payload["articles"] *= 2
        with self.assertRaises(ValueError):
            read_snapshot(payload)

    def test_preview_uses_snapshot_without_smtp_or_ledger(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "sample.json"
            path.write_text(json.dumps(sample()), encoding="utf-8")
            with patch("sys.argv", ["briefing", "--input", str(path), "--email-check"]), \
                 patch("briefing.__main__.load_dotenv"), \
                 patch("briefing.__main__.send_via_smtp") as smtp, \
                 patch("briefing.__main__.DeliveryLedger") as ledger, \
                 patch("sys.stdout"), patch("sys.stderr"):
                self.assertEqual(main(), 0)
                smtp.assert_not_called()
                ledger.assert_not_called()

    def test_send_and_preview_are_mutually_exclusive(self):
        with patch("sys.argv", ["briefing", "--input", "unused", "--send", "--email-check"]), \
             patch("briefing.__main__.load_dotenv"), patch("sys.stderr"):
            with self.assertRaises(SystemExit) as error:
                main()
            self.assertEqual(error.exception.code, 2)

    def test_saved_live_results_send_once_with_preserved_metadata(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "sample.json"
            database = Path(folder) / "deliveries.sqlite"
            path.write_text(json.dumps(sample()), encoding="utf-8")
            argv = ["briefing", "--input", str(path), "--send", "--to", "test@example.invalid",
                    "--delivery-id", "snapshot-1", "--delivery-db", str(database)]
            env = dict(SMTP_HOST="smtp.example.invalid", SMTP_FROM="test@example.invalid",
                       SMTP_USERNAME="test", SMTP_PASSWORD="mock-only", SMTP_PORT="587")
            with patch("sys.argv", argv), patch.dict(os.environ, env), \
                 patch("briefing.__main__.load_dotenv"), \
                 patch("briefing.__main__.send_via_smtp", return_value=None) as smtp, \
                 patch("sys.stdout"), patch("sys.stderr"):
                self.assertEqual(main(), 0)
                self.assertEqual(main(), 0)
                smtp.assert_called_once()
                body = smtp.call_args.args[0].get_content()
                self.assertIn("GDELT: failed", body)
                self.assertIn("2026-11-26T12:00:00+09:00", body)
                self.assertIn("MSIT", body)
                self.assertEqual(DeliveryLedger(database).get("snapshot-1").status, "sent")
