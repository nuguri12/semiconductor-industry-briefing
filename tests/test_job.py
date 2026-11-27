import copy
from datetime import datetime, timezone
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from briefing.job import execute
from briefing.schedule import make_plan
from briefing.delivery import DeliveryLedger, DeliveryUnknown


class MemoryStore:
    """Test double of persistent claim/replay semantics, not a SQL simulation."""
    def __init__(self):
        self.state = None
        self.saved = None

    def claim_schedule(self, plan):
        if self.saved:
            return None, copy.deepcopy(self.saved)
        if self.state:
            raise ValueError('already claimed')
        self.state = 'collecting'
        return 'claim', None

    def complete_schedule(self, claim, result, subject, body):
        self.saved = ('briefing', copy.deepcopy(result), subject, body)
        self.state = 'ready'
        return 'briefing'

    def fail_schedule(self, claim):
        self.state = 'failed'


class JobTests(unittest.TestCase):
    def setUp(self):
        self.plan = make_plan('2026-11-27T08:10:00+09:00', 'chips')
        self.now = datetime(2026, 11, 27, 2, tzinfo=timezone.utc)
        self.collected = dict(articles=[dict(title='Chips', url='https://example.test/news',
                             source='MSIT', provider='MSIT RSS', observed_at=None,
                             published_at='2026-11-26', published_precision='date')],
                              sources={'GDELT': 'failed', 'MSIT RSS': 'ok', 'MOTIR RSS': 'ok'},
                              source_details={}, rejected=0, limit_reached=False)

    def test_dry_run_no_delivery_and_artifacts_do_not_include_recipient(self):
        sender, ledger = Mock(), Mock()
        with tempfile.TemporaryDirectory() as folder, \
             patch('briefing.job.collect_sources', return_value=self.collected):
            report = execute(self.plan, folder, now=self.now, recipient='private@example.invalid',
                             sender=sender, ledger_factory=ledger)
            self.assertEqual(report['status'], 'dry_run')
            self.assertIn('날짜만 제공된 자료', (Path(folder) / 'preview.txt').read_text(encoding='utf-8'))
            for file in Path(folder).iterdir():
                self.assertNotIn('private@example.invalid', file.read_text(encoding='utf-8'))
        sender.assert_not_called()
        ledger.assert_not_called()

    def test_db_replay_does_not_collect_or_send_twice(self):
        store, sender = MemoryStore(), Mock(return_value=None)
        with tempfile.TemporaryDirectory() as folder, \
             patch('briefing.job.collect_sources', return_value=self.collected) as collect:
            ledger = DeliveryLedger(Path(folder) / 'ledger.sqlite')
            kwargs = dict(store=store, send=True, recipient='test@example.invalid', sender=sender,
                          ledger_factory=lambda *_: ledger, now=self.now)
            a = execute(self.plan, Path(folder) / 'first', **kwargs)
            b = execute(self.plan, Path(folder) / 'retry', **kwargs)
            self.assertEqual(a['status'], 'sent')
            self.assertEqual(b['status'], 'sent')
            self.assertTrue(b['reused'])
            self.assertEqual((Path(folder) / 'first/preview.txt').read_bytes(),
                             (Path(folder) / 'retry/preview.txt').read_bytes())
            collect.assert_called_once()
            sender.assert_called_once()

    def test_unknown_replay_is_not_sent(self):
        store, sender = MemoryStore(), Mock(side_effect=DeliveryUnknown('lost response'))
        with tempfile.TemporaryDirectory() as folder, patch('briefing.job.collect_sources', return_value=self.collected):
            ledger = DeliveryLedger(Path(folder) / 'ledger.sqlite')
            for _ in range(2):
                result = execute(self.plan, Path(folder) / 'out', store=store, send=True,
                                 recipient='test@example.invalid', sender=sender,
                                 ledger_factory=lambda *_: ledger, now=self.now)
                self.assertEqual(result['status'], 'unknown')
            sender.assert_called_once()

    def test_same_window_different_slot_reuses_original_without_resending(self):
        store, sender = MemoryStore(), Mock(return_value=None)
        later = make_plan('2026-11-27T08:20:00+09:00', 'chips')
        with tempfile.TemporaryDirectory() as folder, patch('briefing.job.collect_sources', return_value=self.collected) as collect:
            ledger = DeliveryLedger(Path(folder) / 'ledger.sqlite')
            kwargs = dict(store=store, send=True, recipient='test@example.invalid', sender=sender,
                          ledger_factory=lambda *_: ledger, now=self.now)
            execute(self.plan, folder, **kwargs)
            original = (Path(folder) / 'preview.txt').read_bytes()
            report = execute(later, folder, **kwargs)
            self.assertTrue(report['reused'])
            self.assertEqual((Path(folder) / 'preview.txt').read_bytes(), original)
            saved = json.loads((Path(folder) / 'snapshot.json').read_text(encoding='utf-8'))
            self.assertEqual(saved['schedule'], self.plan)
            collect.assert_called_once()
            sender.assert_called_once()

    def test_invalid_records_fail_without_saving_or_sending(self):
        self.collected.update(articles=[], rejected=1)
        store, sender, ledger = MemoryStore(), Mock(), Mock()
        with tempfile.TemporaryDirectory() as folder, patch('briefing.job.collect_sources', return_value=self.collected):
            with self.assertRaises(ValueError):
                execute(self.plan, folder, store=store, send=True, recipient='test@example.invalid',
                        sender=sender, ledger_factory=ledger, now=self.now)
            self.assertEqual(json.loads((Path(folder) / 'report.json').read_text())['status'], 'failed')
        self.assertEqual(store.state, 'failed')
        self.assertIsNone(store.saved)
        sender.assert_not_called()
        ledger.assert_not_called()

    def test_replay_still_rejects_different_query(self):
        store, sender = MemoryStore(), Mock()
        with tempfile.TemporaryDirectory() as folder, patch('briefing.job.collect_sources', return_value=self.collected):
            execute(self.plan, folder, store=store, now=self.now)
            different = make_plan('2026-11-27T08:10:00+09:00', 'robots')
            with self.assertRaises(ValueError):
                execute(different, folder, store=store, send=True, recipient='test@example.invalid',
                        sender=sender, ledger_factory=Mock(), now=self.now)
        sender.assert_not_called()

    def test_failed_rerun_removes_only_previous_artifacts(self):
        with tempfile.TemporaryDirectory() as folder, patch('briefing.job.collect_sources', return_value=self.collected):
            execute(self.plan, folder, now=self.now)
            keep = Path(folder) / 'keep.txt'
            keep.write_text('keep')
            self.collected.update(articles=[], sources={'GDELT': 'failed'})
            with self.assertRaises(ValueError):
                execute(self.plan, folder, now=self.now)
            self.assertFalse((Path(folder) / 'snapshot.json').exists())
            self.assertFalse((Path(folder) / 'preview.txt').exists())
            self.assertEqual(keep.read_text(), 'keep')
            self.assertEqual(json.loads((Path(folder) / 'report.json').read_text())['status'], 'failed')

    def test_db_claim_failure_blocks_collection_and_send(self):
        store, sender = Mock(), Mock()
        store.claim_schedule.side_effect = ValueError('db unavailable')
        with tempfile.TemporaryDirectory() as folder, patch('briefing.job.collect_sources') as collect:
            with self.assertRaises(ValueError):
                execute(self.plan, folder, store=store, send=True, recipient='test@example.invalid',
                        sender=sender, ledger_factory=Mock(), now=self.now)
            self.assertEqual(json.loads((Path(folder) / 'report.json').read_text())['status'], 'failed')
            collect.assert_not_called()
            sender.assert_not_called()

    def test_failure_to_save_blocks_smtp(self):
        store, sender = MemoryStore(), Mock()
        store.complete_schedule = Mock(side_effect=ValueError('write failed'))
        with tempfile.TemporaryDirectory() as folder, patch('briefing.job.collect_sources', return_value=self.collected):
            with self.assertRaises(ValueError):
                execute(self.plan, folder, store=store, send=True, recipient='test@example.invalid',
                        sender=sender, ledger_factory=Mock(), now=self.now)
        sender.assert_not_called()
        self.assertEqual(store.state, 'failed')

    def test_empty_result_never_constructs_delivery(self):
        self.collected['articles'] = []
        sender, ledger = Mock(), Mock()
        with tempfile.TemporaryDirectory() as folder, patch('briefing.job.collect_sources', return_value=self.collected):
            report = execute(self.plan, folder, store=MemoryStore(), send=True, recipient='test@example.invalid',
                             sender=sender, ledger_factory=ledger, now=self.now)
        self.assertEqual(report['status'], 'empty')
        ledger.assert_not_called()
        sender.assert_not_called()

    def test_all_sources_failed_marks_claim_failed(self):
        self.collected.update(articles=[], sources={'GDELT': 'failed'})
        store = MemoryStore()
        with tempfile.TemporaryDirectory() as folder, patch('briefing.job.collect_sources', return_value=self.collected):
            with self.assertRaises(ValueError):
                execute(self.plan, folder, store=store, now=self.now)
        self.assertEqual(store.state, 'failed')

    def test_future_slot_and_no_db_send_fail_before_collection(self):
        with tempfile.TemporaryDirectory() as folder, patch('briefing.job.collect_sources') as collect:
            with self.assertRaises(ValueError):
                execute(self.plan, folder, now=datetime(2026, 11, 25, tzinfo=timezone.utc))
            with self.assertRaises(ValueError):
                execute(self.plan, folder, send=True, now=self.now)
            collect.assert_not_called()
