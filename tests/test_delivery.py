import tempfile
import unittest
from pathlib import Path
import json

from briefing.delivery import DeliveryLedger, DeliveryUnknown, dispatch
from briefing.__main__ import normalize, render
from briefing.email import build_message, validate_message
from briefing.email import send_via_smtp
from unittest.mock import patch


class DeliveryTests(unittest.TestCase):
    @patch("briefing.email.smtplib.SMTP")
    def test_smtp_sender_requires_starttls_and_sends_message(self, smtp_class):
        result = dict(collected_at="2026-11-21T08:00:00+09:00")
        message = build_message(result, "수집 시각: now\n기사 0건", "review@example.invalid")
        smtp = smtp_class.return_value
        smtp.send_message.return_value = {}
        send_via_smtp(message, "smtp.example.test", 587, "sender", "secret")
        smtp.starttls.assert_called_once()
        smtp.login.assert_called_once_with("sender", "secret")
        smtp.send_message.assert_called_once_with(message)

    @patch("briefing.email.smtplib.SMTP")
    def test_smtp_transport_failure_is_unknown(self, smtp_class):
        from briefing.delivery import DeliveryUnknown
        smtp = smtp_class.return_value
        smtp.send_message.side_effect = TimeoutError("lost response")
        result = dict(collected_at="now")
        with self.assertRaises(DeliveryUnknown):
            send_via_smtp(build_message(result, "body", "review@example.invalid"), "smtp.example.test", 587, "u", "p")

    @patch("briefing.email.smtplib.SMTP")
    def test_smtp_recipient_rejection_is_definite(self, smtp_class):
        import smtplib
        smtp = smtp_class.return_value
        smtp.send_message.side_effect = smtplib.SMTPRecipientsRefused({"x": (550, b"no")})
        with self.assertRaisesRegex(ValueError, "거부"):
            send_via_smtp(build_message({"collected_at": "now"}, "body", "x@example.test"),
                          "smtp.example.test", 587, "u", "p")

    @patch("briefing.email.smtplib.SMTP")
    def test_quit_failure_after_smtp_acceptance_does_not_change_success(self, smtp_class):
        smtp = smtp_class.return_value
        smtp.send_message.return_value = {}
        smtp.close.side_effect = OSError("quit failed")
        self.assertIsNone(send_via_smtp(build_message({"collected_at": "now"}, "body", "review@example.invalid"),
                                        "smtp.example.test", 587, "u", "p"))

    def test_fixture_to_validated_mock_delivery(self):
        fixture = Path(__file__).parent / "fixtures" / "articles.json"
        articles, rejected = normalize(json.loads(fixture.read_text(encoding="utf-8")))
        result = dict(collected_at="2026-11-21T08:00:00+09:00", query="synthetic",
                      articles=articles, rejected=rejected, limit_reached=False)
        message = build_message(result, render(result), "review@example.invalid")
        self.assertEqual(validate_message(message), [])
        with tempfile.TemporaryDirectory() as folder:
            ledger = DeliveryLedger(Path(folder) / "state.sqlite")
            sent = []
            outcome = dispatch(ledger, "offline-test", message.as_bytes(),
                               lambda payload: sent.append(payload) or "mock-1")
            self.assertEqual(outcome.status, "sent")
            self.assertEqual(len(sent), 1)

    def test_dry_run_never_calls_sender(self):
        with tempfile.TemporaryDirectory() as folder:
            ledger = DeliveryLedger(Path(folder) / "state.sqlite")
            result = dispatch(ledger, "daily-1", b"message", lambda _: self.fail("sent"), dry_run=True)
            self.assertEqual(result.status, "dry_run")

    def test_success_is_not_sent_twice(self):
        with tempfile.TemporaryDirectory() as folder:
            ledger = DeliveryLedger(Path(folder) / "state.sqlite")
            calls = []
            sender = lambda message: calls.append(message) or "msg-1"
            first = dispatch(ledger, "daily-1", b"message", sender)
            second = dispatch(ledger, "daily-1", b"message", sender)
            self.assertEqual(first.status, "sent")
            self.assertEqual(second.status, "sent")
            self.assertEqual(len(calls), 1)

    def test_unknown_outcome_is_not_retried(self):
        with tempfile.TemporaryDirectory() as folder:
            ledger = DeliveryLedger(Path(folder) / "state.sqlite")
            calls = []
            def sender(_):
                calls.append(1)
                raise DeliveryUnknown("timeout")
            self.assertEqual(dispatch(ledger, "daily-1", b"message", sender).status, "unknown")
            self.assertEqual(dispatch(ledger, "daily-1", b"message", sender).status, "unknown")
            self.assertEqual(len(calls), 1)

    def test_definite_failure_is_recorded_without_automatic_retry(self):
        with tempfile.TemporaryDirectory() as folder:
            ledger = DeliveryLedger(Path(folder) / "state.sqlite")
            calls = []
            def sender(_):
                calls.append(1)
                raise ValueError("rejected")
            self.assertEqual(dispatch(ledger, "daily-1", b"message", sender).status, "failed")
            self.assertEqual(dispatch(ledger, "daily-1", b"message", sender).status, "failed")
            self.assertEqual(len(calls), 1)


if __name__ == "__main__":
    unittest.main()
