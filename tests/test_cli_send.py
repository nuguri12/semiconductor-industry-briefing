import json
import subprocess
import sys
import tempfile
from pathlib import Path
import unittest


class SendGateTests(unittest.TestCase):
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
