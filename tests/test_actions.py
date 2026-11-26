import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from briefing.actions import main


class ActionsTests(unittest.TestCase):
    def test_delayed_schedule_uses_workflow_creation_not_job_start(self):
        env = dict(BRIEFING_EVENT='schedule', BRIEFING_RUN_CREATED_AT='2026-11-26T23:12:00Z',
                   BRIEFING_QUERY='chips', BRIEFING_HOURS='24')
        with tempfile.TemporaryDirectory() as folder, patch.dict(os.environ, env, clear=True), \
             patch('briefing.actions.Path', return_value=Path(folder)), patch('builtins.print'), \
             patch('briefing.actions.execute') as execute:
            execute.return_value = dict(status='dry_run', started_at='2026-11-27T00:20:00.500000+00:00')
            self.assertEqual(main(), 0)
            plan = execute.call_args.args[0]
            self.assertEqual(plan['window_end'], '2026-11-26T23:00:00+00:00')
            self.assertEqual(execute.call_args.kwargs, {})
            report = json.loads((Path(folder) / 'report.json').read_text())
            self.assertEqual(report['workflow_creation_delay_seconds'], 120)
            self.assertEqual(report['runner_delay_seconds'], 4080.5)

    def test_manual_invalid_slot_fails_before_execution(self):
        env = dict(BRIEFING_EVENT='workflow_dispatch', BRIEFING_RUN_CREATED_AT='2026-11-26T23:12:00Z',
                   BRIEFING_QUERY='chips', BRIEFING_SCHEDULED_FOR='not-a-date')
        with tempfile.TemporaryDirectory() as folder, patch.dict(os.environ, env, clear=True), \
             patch('briefing.actions.Path', return_value=Path(folder)), patch('builtins.print'), \
             patch('briefing.actions.execute') as execute:
            self.assertEqual(main(), 1)
            execute.assert_not_called()
            self.assertEqual(json.loads((Path(folder) / 'report.json').read_text())['status'], 'failed')
