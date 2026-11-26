"""Run only against an isolated TLS test database explicitly configured by its owner."""
import os
import unittest
import uuid
from concurrent.futures import ThreadPoolExecutor

from briefing.db import PostgresStore, PostgresLedger, connection, migrate, snapshot_key
from briefing.delivery import dispatch, DeliveryUnknown
from test_snapshot import sample
from briefing.schedule import make_plan


@unittest.skipUnless(os.environ.get('BRIEFING_TEST_DATABASE_URL'), 'Isolated PostgreSQL test URL not configured')
class PostgresIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.url = os.environ['BRIEFING_TEST_DATABASE_URL']
        migrate(cls.url)
        migrate(cls.url)

    def setUp(self):
        self.result = sample()
        self.result['query'] = 'integration-' + str(uuid.uuid4())
        self.store = PostgresStore(self.url)

    def tearDown(self):
        with connection(self.url) as db:
            row = db.execute('SELECT id FROM briefing.runs WHERE run_key=%s',
                             (snapshot_key(self.result),)).fetchone()
            if row:
                db.execute('DELETE FROM briefing.deliveries WHERE briefing_id IN '
                           '(SELECT id FROM briefing.briefings WHERE run_id=%s)', (row[0],))
                db.execute('DELETE FROM briefing.briefings WHERE run_id=%s', (row[0],))
                db.execute('DELETE FROM briefing.runs WHERE id=%s', (row[0],))

    def test_concurrent_save_and_claim_have_one_winner(self):
        with ThreadPoolExecutor(max_workers=2) as pool:
            ids = list(pool.map(lambda _: self.store.save(self.result, 'subject', 'body'), range(2)))
        self.assertEqual(ids[0], ids[1])
        self.assertEqual(self.store.load(ids[0])[0], self.result)
        ledger = PostgresLedger(self.url, ids[0], 'test@example.invalid')
        key = str(uuid.uuid4())
        with ThreadPoolExecutor(max_workers=2) as pool:
            claimed = list(pool.map(lambda _: ledger.claim(key), range(2)))
        self.assertEqual(sum(claimed), 1)

    def test_unknown_is_not_retried(self):
        bid = self.store.save(self.result, 'subject', 'body')
        ledger = PostgresLedger(self.url, bid, 'test@example.invalid')
        calls = []
        def sender(_):
            calls.append(1)
            raise DeliveryUnknown()
        key = str(uuid.uuid4())
        self.assertEqual(dispatch(ledger, key, b'mock', sender).status, 'unknown')
        self.assertEqual(dispatch(ledger, key, b'mock', sender).status, 'unknown')
        self.assertEqual(len(calls), 1)

    def test_changed_body_rolls_back(self):
        bid = self.store.save(self.result, 'subject', 'body')
        with self.assertRaises(ValueError):
            self.store.save(self.result, 'subject', 'changed')
        self.assertEqual(self.store.load(bid)[2], 'body')

    def test_schedule_claim_replay_and_completion(self):
        self.result['schedule'] = make_plan('2026-11-27T08:10:00+09:00', self.result['query'])
        plan = self.result['schedule']
        claim_id, replay = self.store.claim_schedule(plan)
        self.assertIsNone(replay)
        with self.assertRaises(ValueError):
            self.store.claim_schedule(plan)
        bid = self.store.complete_schedule(claim_id, self.result, 'subject', 'body')
        claim, saved = self.store.claim_schedule(plan)
        self.assertIsNone(claim)
        self.assertEqual(saved, (bid, self.result, 'subject', 'body'))

    def test_failed_schedule_not_automatically_reclaimed(self):
        self.result['schedule'] = make_plan('2026-11-27T08:10:00+09:00', self.result['query'])
        plan = self.result['schedule']
        claim_id, _ = self.store.claim_schedule(plan)
        self.store.fail_schedule(claim_id)
        with self.assertRaises(ValueError):
            self.store.claim_schedule(plan)
