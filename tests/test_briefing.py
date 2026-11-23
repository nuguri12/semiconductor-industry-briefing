import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from datetime import datetime, timezone, timedelta
from email.utils import format_datetime
from briefing.__main__ import collect, load_dotenv, normalize, render, retry_delay
from briefing.email import build_message, validate_message


class BriefingTests(unittest.TestCase):
    def test_load_dotenv_keeps_existing_environment_values(self):
        import os
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as directory:
            env_file = Path(directory) / ".env"
            env_file.write_text("MVP_TEST_ENV=new\n# comment\n", encoding="utf-8")
            with patch.dict(os.environ, {"MVP_TEST_ENV": "existing"}):
                load_dotenv(env_file)
                self.assertEqual(os.environ["MVP_TEST_ENV"], "existing")
            with patch.dict(os.environ, {}, clear=False):
                os.environ.pop("MVP_TEST_ENV", None)
                load_dotenv(env_file)
                self.assertEqual(os.environ["MVP_TEST_ENV"], "new")
                os.environ.pop("MVP_TEST_ENV", None)

    def test_email_message_validation_and_no_sender(self):
        result = dict(collected_at="2026-11-21T08:00:00+09:00", query="sample",
                      articles=[dict(title="Test", source="example.com",
                                     observed_at=None, url="https://example.com/a")],
                      rejected=0, limit_reached=False)
        message = build_message(result, render(result), "review@example.invalid")
        self.assertEqual(validate_message(message), [])
        self.assertEqual(message["To"], "review@example.invalid")
        self.assertEqual(message["From"], None)

    def test_email_rejects_missing_fields_but_accepts_http_source_link(self):
        from email.message import EmailMessage
        message = EmailMessage()
        message["To"] = "test@example.test"
        message["Subject"] = "test"
        message.set_content("수집 시각: now\n기사 1건\n원문: http://example.com")
        errors = validate_message(message)
        self.assertEqual(errors, [])

    def test_retry_after(self):
        self.assertEqual(retry_delay("12"), 12)
        self.assertEqual(retry_delay("broken"), 5)
        self.assertEqual(retry_delay(None), 5)
        deadline = format_datetime(datetime.now(timezone.utc) + timedelta(seconds=30))
        self.assertTrue(28 <= retry_delay(deadline) <= 30)

    @patch("briefing.__main__.time.sleep")
    @patch("briefing.__main__.urlopen")
    def test_retry_only_once(self, opener, sleep):
        opener.side_effect = [HTTPError("url", 429, "limited", {"Retry-After": "12"}, None),
                              HTTPError("url", 429, "limited", {}, None)]
        with self.assertRaises(HTTPError):
            collect("Infineon", 24, 25)
        self.assertEqual(opener.call_count, 2)
        sleep.assert_called_once_with(12)

    @patch("briefing.__main__.time.sleep")
    @patch("briefing.__main__.urlopen")
    def test_long_retry_after_stops(self, opener, sleep):
        opener.side_effect = HTTPError("url", 429, "limited", {"Retry-After": "120"}, None)
        with self.assertRaisesRegex(ValueError, "120"):
            collect("Infineon", 24, 25)
        self.assertEqual(opener.call_count, 1)
        sleep.assert_not_called()

    @patch("briefing.__main__.time.sleep")
    @patch("briefing.__main__.urlopen")
    def test_permanent_error_not_retried(self, opener, sleep):
        opener.side_effect = HTTPError("url", 403, "forbidden", {}, None)
        with self.assertRaises(HTTPError):
            collect("Infineon", 24, 25)
        self.assertEqual(opener.call_count, 1)
        sleep.assert_not_called()

    @patch("briefing.__main__.time.sleep")
    @patch("briefing.__main__.urlopen")
    def test_retry_then_success(self, opener, sleep):
        response = opener.return_value
        response.__enter__.return_value.read.return_value = b'{"articles":[]}'
        opener.side_effect = [HTTPError("url", 503, "unavailable", {}, None), response]
        self.assertEqual(collect("Infineon", 24, 25), {"articles": []})
        sleep.assert_called_once_with(5)

    def test_invalid_urls_and_times(self):
        urls = ["https://example.com:bad/a", "https://example.com:70000/a",
                "https://example.com/\x01x", "https://user:password@example.com/a",
                "https://example.com\\other", "https://example.com:0/a"]
        rows, rejected = normalize({"articles": [{"title": "x", "url": url} for url in urls]})
        self.assertEqual(rows, [])
        self.assertEqual(rejected, len(urls))
        for stamp in [None, 123, "20261120T2300Z", "20260230T230000Z"]:
            rows, _ = normalize({"articles": [{"title": "x", "url": "https://example.com", "seendate": stamp}]})
            self.assertIsNone(rows[0]["observed_at"])

    def test_all_rejected_message(self):
        result = dict(articles=[], rejected=3, query="sample", collected_at="now", limit_reached=False)
        self.assertIn("모든 수집 항목이 검증에서 제외", render(result))

    def test_normalize_and_timestamp(self):
        rows, rejected = normalize({"articles": [
            {"title": " A &amp; B\n news ", "url": "https://example.com/a",
             "seendate": "20261120T230000Z"},
            {"title": "unsafe", "url": "javascript:alert(1)"},
            {"title": "missing time", "url": "https://example.com/b"}]})
        self.assertEqual(rejected, 1)
        self.assertEqual(rows[0]["title"], "A & B news")
        self.assertEqual(rows[0]["observed_at"], "2026-11-21T08:00:00+09:00")
        self.assertIsNone(rows[0]["published_at"])
        self.assertIsNone(rows[1]["observed_at"])

    def test_bad_response_is_not_empty_success(self):
        with self.assertRaises(ValueError):
            normalize({"error": "limit"})

    def test_empty_message(self):
        result = dict(articles=[], rejected=0, query="sample",
                      collected_at="now", limit_reached=False)
        self.assertIn("표시할 기사가 없습니다", render(result))

    @patch("briefing.__main__.urlopen")
    def test_fetch(self, opener):
        opener.return_value.__enter__.return_value.read.return_value = b'{"articles":[]}'
        self.assertEqual(collect("Infineon", 24, 25), {"articles": []})
        self.assertIn("query=Infineon", opener.call_args.args[0].full_url)
        opener.return_value.__enter__.return_value.read.return_value = b'Rate limit'
        with self.assertRaises(ValueError):
            collect("Infineon", 24, 25)
        opener.return_value.__enter__.return_value.read.return_value = b'x' * 5_000_001
        with self.assertRaisesRegex(ValueError, "5 MB"):
            collect("Infineon", 24, 25)


if __name__ == "__main__":
    unittest.main()
