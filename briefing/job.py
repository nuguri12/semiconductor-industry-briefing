"""Fixed-window batch. Default is dry-run; sending requires persistent PostgreSQL."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path

from .__main__ import collect_sources, read_snapshot, render, load_dotenv
from .db import PostgresStore, PostgresLedger
from .delivery import dispatch
from .email import build_message, validate_message, add_sender, send_via_smtp
from .schedule import make_plan, validate_plan, timestamp, delivery_key


def in_window(article, plan):
    start, end = timestamp(plan['window_start']), timestamp(plan['window_end'])
    value = article.get('published_at') or article.get('observed_at')
    if not value:
        return False
    if article.get('published_precision') == 'date':
        from .schedule import KST
        day = datetime.fromisoformat(value).date()
        return start.astimezone(KST).date() <= day <= end.astimezone(KST).date()
    when = datetime.fromisoformat(value)
    return when.tzinfo is not None and start <= when < end


def collect_snapshot(plan, now):
    collected = collect_sources(plan['query'], plan['hours'], plan['limit'],
                                window_end=timestamp(plan['window_end']))
    articles = [a for a in collected['articles'] if in_window(a, plan)]
    result = dict(collected, articles=articles, window_excluded=len(collected['articles']) - len(articles),
                  schema_version=1, collected_at=now.isoformat(), query=plan['query'],
                  hours=plan['hours'], schedule=plan)
    result['status'] = ('invalid_records' if result['rejected'] and not articles else
                        'partial' if result['rejected'] or any(s != 'ok' for s in result['sources'].values()) else
                        'ok' if articles else 'empty')
    return read_snapshot(result)


def execute(plan, output, *, store=None, send=False, recipient=None, sender=None, now=None,
            ledger_factory=None):
    validate_plan(plan)
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None or timestamp(plan['scheduled_for']) > now:
        raise ValueError('Cannot execute a future scheduled slot')
    if send and (store is None or not recipient or sender is None or ledger_factory is None):
        raise ValueError('Sending requires database, recipient and configured sender')
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    report = dict(run_key=plan['run_key'], scheduled_for=plan['scheduled_for'], started_at=now.isoformat(),
                  start_delay_seconds=(now - timestamp(plan['scheduled_for'])).total_seconds(),
                  mode='send' if send else 'dry_run', status='failed')
    claim_id = None
    try:
        replay = None
        if store:
            claim_id, replay = store.claim_schedule(plan)
        if replay:
            briefing_id, result, subject, body = replay
            read_snapshot(result)
            if result.get('schedule') != plan or body != render(result):
                raise ValueError('Stored briefing does not match this scheduled plan')
        else:
            result = collect_snapshot(plan, now)
            body = render(result)
            subject = str(build_message(result, body)['Subject'])
            briefing_id = None
        message = build_message(result, body, recipient or 'review@example.invalid')
        if str(message['Subject']) != subject or validate_message(message):
            raise ValueError('Scheduled email validation failed')
        report.update(articles=len(result['articles']), sources=result['sources'], reused=bool(replay))
        if all(s == 'failed' for s in result['sources'].values()):
            raise ValueError('All news sources failed')
        if store and not replay:
            briefing_id = store.complete_schedule(claim_id, result, subject, body)
            claim_id = None
        (output / 'snapshot.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
        # Artifacts contain news metadata only, never recipients or transport credentials.
        (output / 'preview.txt').write_text(subject + '\n\n' + body, encoding='utf-8')
        if not result['articles']:
            report['status'] = 'empty'
        elif not send:
            report['status'] = 'dry_run'
        else:
            ledger = ledger_factory(briefing_id, recipient)
            outcome = dispatch(ledger, delivery_key(plan, recipient), message, sender)
            report['status'] = outcome.status
        return report
    except Exception as error:
        report['error_type'] = type(error).__name__
        if store and claim_id:
            try:
                store.fail_schedule(claim_id)
            except Exception:
                report['state_recording_failed'] = True
        raise
    finally:
        report['finished_at'] = datetime.now(timezone.utc).isoformat()
        (output / 'report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scheduled-for', required=True, help='ISO timestamp with timezone')
    parser.add_argument('--query', required=True)
    parser.add_argument('--hours', type=int, default=24)
    parser.add_argument('--limit', type=int, default=25)
    parser.add_argument('--output', default='output/scheduled')
    parser.add_argument('--store-db', action='store_true')
    parser.add_argument('--send', action='store_true')
    parser.add_argument('--to')
    args = parser.parse_args()
    load_dotenv()
    try:
        plan = make_plan(args.scheduled_for, args.query, args.hours, args.limit)
        store = PostgresStore(os.getenv('DATABASE_URL')) if args.store_db else None
        sender = None
        if args.send:
            if not args.store_db or not args.to:
                raise ValueError('--send requires --store-db and --to')
            required = ['SMTP_HOST', 'SMTP_FROM', 'SMTP_USERNAME', 'SMTP_PASSWORD']
            if not all(os.getenv(k) for k in required):
                raise ValueError('SMTP configuration is missing')
            port = int(os.getenv('SMTP_PORT', '587'))
            if not 1 <= port <= 65535:
                raise ValueError('Invalid SMTP port')
            def sender(message):
                add_sender(message, os.environ['SMTP_FROM'])
                return send_via_smtp(message, os.environ['SMTP_HOST'], port,
                                     os.environ['SMTP_USERNAME'], os.environ['SMTP_PASSWORD'])
        report = execute(plan, args.output, store=store, send=args.send, recipient=args.to, sender=sender,
                         ledger_factory=lambda bid, to: PostgresLedger(os.getenv('DATABASE_URL'), bid, to))
        print(json.dumps(report))
        return 0 if report['status'] in ('dry_run', 'empty', 'sent') else 2
    except (OSError, ValueError) as error:
        # Do not print raw driver/network exception text or credentials.
        print(json.dumps(dict(status='failed', error_type=type(error).__name__)))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
