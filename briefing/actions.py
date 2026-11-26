"""GitHub Actions adapter: dry-run only, with no DB or SMTP credentials required."""
import json
import os
from datetime import datetime
from pathlib import Path

from .job import execute
from .schedule import github_daily_slot, make_plan, timestamp


def main():
    output = Path('output/scheduled')
    try:
        event = os.environ.get('BRIEFING_EVENT')
        created_at = os.environ['BRIEFING_RUN_CREATED_AT']
        timestamp(created_at)
        if event == 'schedule':
            scheduled_for = github_daily_slot(created_at)
        elif event == 'workflow_dispatch':
            scheduled_for = os.environ.get('BRIEFING_SCHEDULED_FOR', '')
        else:
            raise ValueError('Unsupported Actions event')
        plan = make_plan(scheduled_for, os.environ.get('BRIEFING_QUERY', ''),
                         int(os.environ.get('BRIEFING_HOURS', '24')),
                         int(os.environ.get('BRIEFING_LIMIT', '25')))
        # Never add send/database parameters here; deployment requires a separately reviewed path.
        report = execute(plan, output)
        report.update(event=event, slot_inferred_from_workflow_creation=(event == 'schedule'),
                      workflow_created_at=created_at,
                      workflow_creation_delay_seconds=(timestamp(created_at) - timestamp(plan['scheduled_for'])).total_seconds(),
                      runner_delay_seconds=(datetime.fromisoformat(report['started_at']) - timestamp(created_at)).total_seconds())
        (output / 'report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
        print(json.dumps(report))
        return 0
    except (KeyError, OSError, ValueError) as error:
        failure = dict(status='failed', error_type=type(error).__name__)
        try:
            output.mkdir(parents=True, exist_ok=True)
            path = output / 'report.json'
            if path.exists():
                failure.update(json.loads(path.read_text(encoding='utf-8')))
            failure['status'] = 'failed'
            path.write_text(json.dumps(failure, indent=2), encoding='utf-8')
        except (OSError, ValueError):
            pass
        print(json.dumps(failure))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
