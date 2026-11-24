import unittest
from unittest.mock import patch

import briefing.__main__ as app


class MultiSourceTests(unittest.TestCase):
    def test_deepsearch_response_maps_to_shared_article_fields(self):
        normalize_deepsearch = getattr(app, "normalize_deepsearch", None)
        self.assertTrue(callable(normalize_deepsearch), "DeepSearch normalization is not implemented")
        payload = {"data": [{
            "title": "반도체 장비 투자 확대",
            "publisher": "Example News",
            "content_url": "https://news.example.test/article/1",
            "published_at": "2026-11-24T08:30:00+09:00",
            "summary": "이 내용은 메일로 복사되면 안 됩니다.",
        }]}

        articles, rejected = normalize_deepsearch(payload)

        self.assertEqual(rejected, 0)
        self.assertEqual(articles, [{
            "title": "반도체 장비 투자 확대",
            "url": "https://news.example.test/article/1",
            "source": "Example News",
            "provider": "DeepSearch",
            "observed_at": None,
            "published_at": "2026-11-24T08:30:00+09:00",
            "language": "ko",
        }])

    def test_email_preview_labels_deepsearch_timestamp_as_publication_time(self):
        article, _ = app.normalize_deepsearch({"data": [{
            "title": "Headline", "publisher": "Example News",
            "content_url": "https://news.example.test/article/1",
            "published_at": "2026-11-24T08:30:00+09:00",
        }]}, now=app.datetime(2026, 11, 24, 9, 0, tzinfo=app.KST))
        body = app.render({
            "collected_at": "2026-11-24T09:00:00+09:00", "query": "semiconductor",
            "articles": article, "rejected": 0, "limit_reached": False,
            "sources": {"DeepSearch": "ok"},
        })

        self.assertIn("발행 시각: 2026-11-24T08:30:00+09:00", body)
        self.assertNotIn("관측 시각: 확인 불가", body)

    @patch("briefing.__main__.collect")
    @patch("briefing.__main__.collect_deepsearch", create=True)
    def test_collect_sources_uses_both_and_deduplicates_by_url(self, deepsearch, gdelt):
        collect_sources = getattr(app, "collect_sources", None)
        self.assertTrue(callable(collect_sources), "multi-source collection is not implemented")
        gdelt.return_value = {"articles": [{
            "title": "GDELT headline", "url": "https://news.example.test/a",
            "seendate": "20261124T000000Z", "language": "English",
        }]}
        deepsearch.return_value = {"data": [{
            "title": "DeepSearch headline", "publisher": "Example News",
            "content_url": "https://news.example.test/a",
            "published_at": "2026-11-24T09:00:00+09:00",
        }, {
            "title": "Second headline", "publisher": "Other News",
            "content_url": "https://other.example.test/b",
            "published_at": "2026-11-24T09:00:00+09:00",
        }]}

        result = collect_sources("semiconductor OR automation", 24, 10, "secret-test-key")

        gdelt.assert_called_once_with("semiconductor OR automation", 24, 10)
        deepsearch.assert_called_once_with("semiconductor OR automation", 24, 10, "secret-test-key")
        self.assertEqual([a["url"] for a in result["articles"]], [
            "https://news.example.test/a", "https://other.example.test/b",
        ])
        self.assertEqual(result["articles"][0]["provider"], "GDELT")
        self.assertEqual(result["articles"][1]["provider"], "DeepSearch")
        self.assertEqual(result["sources"], {"GDELT": "ok", "DeepSearch": "ok"})

    @patch("briefing.__main__.collect")
    @patch("briefing.__main__.collect_deepsearch", create=True)
    def test_one_source_failure_keeps_other_results_and_marks_partial(self, deepsearch, gdelt):
        collect_sources = getattr(app, "collect_sources", None)
        self.assertTrue(callable(collect_sources), "multi-source collection is not implemented")
        gdelt.side_effect = OSError("provider unavailable")
        deepsearch.return_value = {"data": [{
            "title": "One result", "publisher": "Example News",
            "content_url": "https://news.example.test/a",
            "published_at": "2026-11-24T09:00:00+09:00",
        }]}

        result = collect_sources("semiconductor", 24, 10, "secret-test-key")

        self.assertEqual(result["sources"], {"GDELT": "failed", "DeepSearch": "ok"})
        self.assertEqual(len(result["articles"]), 1)

    @patch("briefing.__main__.collect")
    @patch("briefing.__main__.collect_deepsearch", create=True)
    def test_missing_deepsearch_key_does_not_expose_key_or_discard_gdelt(self, deepsearch, gdelt):
        collect_sources = getattr(app, "collect_sources", None)
        self.assertTrue(callable(collect_sources), "multi-source collection is not implemented")
        gdelt.return_value = {"articles": [{
            "title": "GDELT headline", "url": "https://news.example.test/a",
            "seendate": "20261124T000000Z", "language": "English",
        }]}

        result = collect_sources("semiconductor", 24, 10, None)

        deepsearch.assert_not_called()
        self.assertEqual(result["sources"], {
            "GDELT": "ok", "DeepSearch": "skipped_not_configured",
        })
        self.assertEqual(len(result["articles"]), 1)


if __name__ == "__main__":
    unittest.main()
