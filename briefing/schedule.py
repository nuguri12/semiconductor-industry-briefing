"""Deterministic daily windows shared by manual and scheduled execution."""
from datetime import datetime, timedelta, timezone
import hashlib
import json

KST = timezone(timedelta(hours=9))
PIPELINE_VERSION = 'scheduled-v1-gdelt-msit-motir'


def timestamp(value):
    if not isinstance(value, str):
        raise ValueError('Timestamp must be an ISO string with timezone')
    parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if parsed.tzinfo is None or parsed.microsecond:
        raise ValueError('Timestamp requires timezone and whole seconds')
    return parsed.astimezone(timezone.utc)


def hash_json(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                     separators=(',', ':')).encode()).hexdigest()


def make_plan(scheduled_for, query, hours=24, limit=25):
    when = timestamp(scheduled_for)
    if not isinstance(query, str) or not query.strip():
        raise ValueError('Query is required')
    if type(hours) is not int or not 1 <= hours <= 72 or type(limit) is not int or not 1 <= limit <= 250:
        raise ValueError('Invalid hours or limit')
    # The collection cutoff is the hour preceding the scheduled delivery slot.
    end = when.replace(minute=0, second=0)
    config_hash = hash_json(dict(query=query.strip(), hours=hours, limit=limit,
                                 pipeline_version=PIPELINE_VERSION))
    window = dict(window_start=(end - timedelta(hours=hours)).isoformat(),
                  window_end=end.isoformat(), config_hash=config_hash)
    return dict(window, scheduled_for=when.isoformat(), query=query.strip(), hours=hours,
                limit=limit, pipeline_version=PIPELINE_VERSION, run_key=hash_json(window))


def validate_plan(plan):
    if not isinstance(plan, dict):
        raise ValueError('Invalid schedule plan')
    try:
        expected = make_plan(plan['scheduled_for'], plan['query'], plan['hours'], plan['limit'])
    except (KeyError, TypeError) as error:
        raise ValueError('Incomplete schedule plan') from error
    if plan != expected:
        raise ValueError('Schedule plan does not match its fixed window/configuration')
    return plan


def github_daily_slot(run_created_at):
    """Infer the 08:10 KST slot only within a bounded delay; reruns use original created_at."""
    # shortcut: creation time cannot detect missed days; add independent monitoring before unattended sending.
    created = timestamp(run_created_at).astimezone(KST)
    slot = created.replace(hour=8, minute=10, second=0)
    if slot > created:
        slot -= timedelta(days=1)
    if created - slot > timedelta(hours=6):
        raise ValueError('Ambiguous/late schedule; manually supply the intended scheduled_for')
    return slot.isoformat()


def delivery_key(plan, recipient):
    validate_plan(plan)
    if not isinstance(recipient, str) or not recipient.strip():
        raise ValueError('Recipient is required')
    return 'scheduled-' + hash_json([plan['run_key'], recipient.strip()])
