import io
import unittest
from unittest.mock import patch

import briefing.__main__ as app


class MultiSourceTests(unittest.TestCase):
    @patch("briefing.__main__.collect_msit_rss")
    @patch("briefing.__main__.collect")
    def test_limit_preserves_both_sources_after_deduplication(self, gdelt, rss):
        gdelt.return_value = {"articles": [
            {"title": "A", "url": "https://example.test/a"},
            {"title": "B", "url": "https://example.test/b"},
        ]}
        rss.return_value = ([
            {"title": "A duplicate", "url": "https://example.test/a", "provider": "MSIT RSS"},
            {"title": "C", "url": "https://example.test/c", "provider": "MSIT RSS"},
        ], 0)
        result = app.collect_sources("Infineon", 24, 2)
        self.assertEqual([a["url"] for a in result["articles"]],
                         ["https://example.test/a", "https://example.test/c"])
        self.assertTrue(result["limit_reached"])
        self.assertEqual(result["sources"], {"GDELT": "ok", "MSIT RSS": "ok"})

    @patch("briefing.__main__.collect_msit_rss")
    @patch("briefing.__main__.collect", side_effect=OSError("provider unavailable"))
    def test_failed_source_preserves_other_results(self, gdelt, rss):
        rss.return_value = ([{"title": "A", "url": "https://example.test/a"}], 0)
        result = app.collect_sources("Infineon", 24, 2)
        self.assertEqual(len(result["articles"]), 1)
        self.assertEqual(result["sources"], {"GDELT": "failed", "MSIT RSS": "ok"})

    @patch("briefing.__main__.collect_msit_rss", side_effect=ValueError("bad XML"))
    @patch("briefing.__main__.collect", side_effect=OSError("provider unavailable"))
    def test_both_failures_remain_visible(self, gdelt, rss):
        result = app.collect_sources("Infineon", 24, 2)
        self.assertEqual(result["articles"], [])
        self.assertEqual(result["sources"], {"GDELT": "failed", "MSIT RSS": "failed"})

    def test_date_only_overlap_without_inventing_midnight(self):
        dates = ["2026.11.25", "2026-11-26", "2026.11.24", "2026.11.27",
                 "2026-11-25T07:59:00+09:00", "2026-11-25T08:00:00+09:00"]
        xml = "<rss><channel>" + "".join(
            f"<item><title>Infineon {i}</title><link>https://example.test/{i}</link>"
            f"<pubDate>{date}</pubDate></item>" for i, date in enumerate(dates)
        ) + "</channel></rss>"
        with patch("briefing.__main__.urlopen", return_value=io.BytesIO(xml.encode())):
            articles, rejected = app.collect_msit_rss(
                "Infineon", 24, 25, now=app.datetime(2026, 11, 26, 8, tzinfo=app.KST))
        self.assertEqual(rejected, 0)
        self.assertEqual([a["url"] for a in articles],
                         ["https://example.test/0", "https://example.test/1", "https://example.test/5"])
        self.assertEqual(articles[0]["published_at"], "2026-11-25")
        self.assertEqual(articles[0]["published_precision"], "date")
        self.assertEqual(articles[2]["published_precision"], "datetime")
        body = app.render(dict(collected_at="test", query="Infineon", articles=articles,
                               rejected=0, limit_reached=False))
        self.assertIn("발행일: 2026-11-25", body)
        self.assertIn("발행 시각: 2026-11-25T08:00:00+09:00", body)

    def test_rss_description_is_not_emitted_even_with_rights_marker(self):
        xml = """<rss><channel><item><title>Infineon</title>
        <link>https://example.test/a</link><pubDate>2026.11.26</pubDate>
        <rights>KOGL Type 1</rights><description>Do not redistribute this text.</description>
        </item></channel></rss>"""
        with patch("briefing.__main__.urlopen", return_value=io.BytesIO(xml.encode())):
            articles, _ = app.collect_msit_rss(
                "Infineon", 24, 25, now=app.datetime(2026, 11, 26, 8, tzinfo=app.KST))
        self.assertEqual(len(articles), 1)
        self.assertNotIn("Do not redistribute", str(articles))
        articles[0]["summary"] = "Do not redistribute this text."
        body = app.render(dict(collected_at="test", query="Infineon", articles=articles,
                               rejected=0, limit_reached=False))
        self.assertNotIn("Do not redistribute", body)


if __name__ == "__main__":
    unittest.main()
