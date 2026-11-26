from contextlib import contextmanager
import os
from pathlib import Path
import json
import tempfile
import unittest
from unittest.mock import Mock, patch

from briefing.db import connection, PostgresStore, PostgresLedger, snapshot_key
from briefing.__main__ import main
from test_snapshot import sample


class DatabaseTests(unittest.TestCase):
    def test_snapshot_key_does_not_depend_on_dictionary_order(self):
        result = sample()
        self.assertEqual(snapshot_key(result), snapshot_key(dict(reversed(list(result.items())))))
        changed = dict(result, collected_at='2026-11-27T12:00:00+09:00')
        self.assertNotEqual(snapshot_key(result), snapshot_key(changed))

    def test_connection_requires_config(self):
        with self.assertRaises(ValueError):
            with connection(None):
                self.fail('connected')

    def test_connection_checks_tls_and_redacts_driver_errors(self):
        import psycopg
        with patch('psycopg.connect', side_effect=psycopg.OperationalError('secret-host-password')) as connect:
            with self.assertRaises(ValueError) as error:
                with connection('secret-url'):
                    pass
            self.assertNotIn('secret', str(error.exception))
            self.assertEqual(connect.call_args.kwargs['sslmode'], 'verify-full')

    def test_same_delivery_key_for_different_content_is_rejected(self):
        db = Mock()
        db.execute.return_value.fetchone.side_effect = [None, ('other-briefing', 'a@example.test')]
        @contextmanager
        def fake_connection(url):
            yield db
        with patch('briefing.db.connection', fake_connection):
            with self.assertRaisesRegex(ValueError, 'identity conflict'):
                PostgresLedger('unused', 'current-briefing', 'a@example.test').claim('same-key')

    def test_changed_snapshot_cannot_overwrite_saved_body(self):
        db = Mock()
        # Existing run and briefing, but different payload/body hash.
        db.execute.return_value.fetchone.side_effect = [None, ('run-id',), ('briefing-id', 'different')]
        @contextmanager
        def fake_connection(url):
            yield db
        with patch('briefing.db.connection', fake_connection):
            with self.assertRaisesRegex(ValueError, 'immutable'):
                PostgresStore('unused').save(sample(), 'subject', 'changed body')

    def test_db_failure_blocks_smtp_and_sqlite_fallback(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'snapshot.json'
            path.write_text(json.dumps(sample()), encoding='utf-8')
            with patch('sys.argv', ['briefing', '--input', str(path), '--store-db', '--send',
                                    '--to', 'a@example.test', '--delivery-id', 'db-test']), \
                 patch.dict(os.environ, {'DATABASE_URL': ''}), \
                 patch('briefing.__main__.load_dotenv'), \
                 patch('briefing.__main__.send_via_smtp') as sender, \
                 patch('briefing.__main__.DeliveryLedger') as local, \
                 patch('sys.stdout'), patch('sys.stderr'):
                self.assertEqual(main(), 1)
                sender.assert_not_called()
                local.assert_not_called()
