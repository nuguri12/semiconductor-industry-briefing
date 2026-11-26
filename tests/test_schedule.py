from datetime import datetime, timezone
import io
import json
import unittest
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

from briefing.schedule import make_plan, validate_plan, github_daily_slot, delivery_key, timestamp
from briefing.__main__ import collect, collect_sources, read_snapshot
from briefing.db import snapshot_key
from briefing.job import in_window
from test_snapshot import sample


class ScheduleTests(unittest.TestCase):
    def setUp(self):
        self.plan = make_plan('2026-11-27T08:10:00+09:00', 'semiconductor')

    def test_fixed_window_is_utc_and_excludes_actual_start_time(self):
        self.assertEqual(self.plan['window_end'], '2026-11-26T23:00:00+00:00')
        self.assertEqual(self.plan['window_start'], '2026-11-25T23:00:00+00:00')
        equivalent = make_plan('2026-11-26T23:10:00Z', 'semiconductor')
        self.assertEqual(self.plan, equivalent)
        self.assertNotEqual(self.plan['run_key'], make_plan('2026-11-27T08:10:00+09:00', 'robotics')['run_key'])

    def test_delayed_github_creation_keeps_slot_and_rejects_ambiguous_delay(self):
        for created in ('2026-11-27T08:10:00+09:00', '2026-11-27T10:20:00+09:00'):
            self.assertEqual(github_daily_slot(created), '2026-11-27T08:10:00+09:00')
        with self.assertRaises(ValueError):
            github_daily_slot('2026-11-27T18:00:00+09:00')
        with self.assertRaises(ValueError):
            github_daily_slot('2026-11-27T08:00:00+09:00')

    def test_bad_timezone_and_tampered_plan_fail(self):
        with self.assertRaises(ValueError):
            make_plan('2026-11-27T08:10:00', 'chips')
        changed = dict(self.plan, window_end='2026-11-27T23:00:00Z')
        with self.assertRaises(ValueError):
            validate_plan(changed)
        for hours in (0, 73, True):
            with self.assertRaises(ValueError):
                make_plan('2026-11-27T08:10:00Z', 'chips', hours=hours)

    def test_delivery_identity_changes_only_with_logical_input_or_recipient(self):
        self.assertEqual(delivery_key(self.plan, 'test@example.invalid'), delivery_key(dict(self.plan), 'test@example.invalid'))
        self.assertNotEqual(delivery_key(self.plan, 'a@example.invalid'), delivery_key(self.plan, 'b@example.invalid'))
        result = sample()
        result.update(query=self.plan['query'], schedule=self.plan)
        first = snapshot_key(result)
        result['collected_at'] = '2026-11-28T01:00:00Z'
        self.assertEqual(first, snapshot_key(result))

    def test_gdelt_uses_absolute_params_not_relative_hours(self):
        with patch('briefing.__main__.urlopen', return_value=io.BytesIO(b'{"articles":[]}')) as opener:
            collect('chips', 24, 5, timestamp(self.plan['window_end']))
        query = parse_qs(urlsplit(opener.call_args.args[0].full_url).query)
        self.assertEqual(query['startdatetime'], ['20261125230000'])
        self.assertEqual(query['enddatetime'], ['20261126230000'])
        self.assertNotIn('timespan', query)

    def test_all_collectors_receive_same_cutoff(self):
        end = timestamp(self.plan['window_end'])
        with patch('briefing.__main__.collect', return_value={'articles': []}) as gdelt, \
             patch('briefing.__main__.collect_msit_rss', return_value=([], 0)) as msit, \
             patch('briefing.__main__.collect_motir_rss', return_value=([], 0)) as motir:
            collect_sources('chips', 24, 5, window_end=end)
        self.assertEqual(gdelt.call_args.kwargs['window_end'], end)
        self.assertEqual(msit.call_args.kwargs['now'], end)
        self.assertEqual(motir.call_args.kwargs['now'], end)

    def test_time_window_edges_and_date_only_overlap(self):
        for stamp, expected in [('2026-11-25T23:00:00Z', True), ('2026-11-26T22:59:59Z', True),
                                ('2026-11-26T23:00:00Z', False), (None, False)]:
            self.assertEqual(in_window(dict(observed_at=stamp), self.plan), expected)
        self.assertTrue(in_window(dict(published_at='2026-11-27', published_precision='date'), self.plan))
        self.assertFalse(in_window(dict(published_at='2026-11-28', published_precision='date'), self.plan))

    def test_snapshot_cannot_override_plan_query(self):
        result = sample()
        result['schedule'] = self.plan
        result['query'] = 'another query'
        with self.assertRaises(ValueError):
            read_snapshot(result)
