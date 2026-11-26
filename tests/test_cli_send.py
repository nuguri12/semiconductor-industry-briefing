import json
import subprocess
import sys
import tempfile
from pathlib import Path
import unittest
import os
from unittest.mock import patch
from briefing.__main__ import main


class SendGateTests(unittest.TestCase):
    def test_file_input_deduplicates_and_obeys_limit(self):
        with tempfile.TemporaryDirectory() as folder:
            sample = Path(folder) / 'sample.json'
            sample.write_text(json.dumps({'articles': [
                {'title': 'A', 'url': 'https://example.com/a'},
                {'title': 'A duplicate', 'url': 'https://example.com/a'},
                {'title': 'B', 'url': 'https://example.com/b'},
                {'title': 'C', 'url': 'https://example.com/c'},
            ]}), encoding='utf-8')
            result = subprocess.run([sys.executable, '-m', 'briefing', '--input',
                                     str(sample), '--limit', '2', '--json'], capture_output=True)
            self.assertEqual(result.returncode, 0)
            payload = json.loads(result.stdout)
            self.assertEqual([row['url'] for row in payload['articles']],
                             ['https://example.com/a', 'https://example.com/b'])
            self.assertTrue(payload['limit_reached'])

    def test_partial_live_collection_sends_once_and_marks_missing_source(self):
        article = dict(title='Infineon test', url='https://example.com/news',
                       source='example.com', provider='MSIT RSS',
                       published_at='2026-11-26', published_precision='date')
        collected = dict(articles=[article], rejected=0,
                         sources={'GDELT': 'failed', 'MSIT RSS': 'ok'}, limit_reached=False)
        with tempfile.TemporaryDirectory() as folder:
            argv = ['briefing', '--query', 'Infineon', '--send', '--to',
                    'test@example.invalid', '--delivery-id', 'partial-1',
                    '--delivery-db', str(Path(folder) / 'deliveries.sqlite')]
            env = dict(SMTP_HOST='smtp.example.invalid', SMTP_PORT='587',
                       SMTP_USERNAME='sender@example.invalid', SMTP_FROM='sender@example.invalid',
                       SMTP_PASSWORD='mock-password')
            with patch('sys.argv', argv), patch.dict(os.environ, env), \
                 patch('briefing.__main__.load_dotenv'), \
                 patch('briefing.__main__.collect_sources', return_value=collected), \
                 patch('briefing.__main__.send_via_smtp', return_value=None) as send, \
                 patch('sys.stdout'), patch('sys.stderr'):
                self.assertEqual(main(), 0)
                self.assertEqual(main(), 0)
            send.assert_called_once()
            body = send.call_args.args[0].get_content()
            self.assertIn('GDELT: failed', body)
            self.assertIn('일부', body)
            self.assertIn('https://example.com/news', body)

    def test_empty_and_invalid_inputs_are_blocked_before_smtp(self):
        with tempfile.TemporaryDirectory() as folder:
            sample = Path(folder) / 'sample.json'
            for rows in ([], [{'title': 'bad', 'url': 'javascript:bad'}]):
                sample.write_text(json.dumps({'articles': rows}), encoding='utf-8')
                result = subprocess.run([sys.executable, '-m', 'briefing', '--input',
                                         str(sample), '--send', '--to', 'test@example.invalid',
                                         '--delivery-id', 'gate-test'], capture_output=True)
                self.assertEqual(result.returncode, 2)
                self.assertIn('발송 보류', result.stderr.decode('utf-8'))
