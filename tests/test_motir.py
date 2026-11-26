import io
import unittest
from unittest.mock import patch

from briefing.__main__ import collect_motir_rss, collect_sources, datetime, KST


class MotirTests(unittest.TestCase):
    def test_official_post_feed_date_and_content_boundary(self):
        xml = b'<rss><channel><item><title>Semiconductor cooperation</title><link>https://www.motir.go.kr/a</link><pubDate>2026-11-26</pubDate><description>Not included</description></item></channel></rss>'
        with patch('briefing.__main__.urlopen', return_value=io.BytesIO(xml)) as opener:
            articles, rejected = collect_motir_rss('semiconductor', 24, 5,
                                                   datetime(2026, 11, 26, 20, tzinfo=KST))
        self.assertEqual(opener.call_args.args[0].get_method(), 'POST')
        self.assertEqual(rejected, 0)
        self.assertEqual(articles[0]['provider'], 'MOTIR RSS')
        self.assertEqual(articles[0]['published_precision'], 'date')
        self.assertNotIn('Not included', str(articles))

    def test_html_is_failure_not_empty_feed(self):
        with patch('briefing.__main__.urlopen', return_value=io.BytesIO(b'<html></html>')):
            with self.assertRaises(ValueError):
                collect_motir_rss('semiconductor', 24, 5)

    def test_third_source_survives_both_others_failing(self):
        article = dict(title='Semiconductor', url='https://www.motir.go.kr/a')
        with patch('briefing.__main__.collect', side_effect=OSError), \
             patch('briefing.__main__.collect_msit_rss', side_effect=OSError), \
             patch('briefing.__main__.collect_motir_rss', return_value=([article], 0)):
            result = collect_sources('semiconductor', 24, 5)
        self.assertEqual(result['articles'], [article])
        self.assertEqual(result['sources']['MOTIR RSS'], 'ok')
