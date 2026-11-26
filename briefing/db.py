"""Explicit PostgreSQL storage for reviewed snapshots; no network on import."""

from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import uuid

from .delivery import DeliveryResult


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                     separators=(',', ':')).encode('utf-8')).hexdigest()


def snapshot_key(result):
    if 'schedule' in result:
        from .schedule import validate_plan
        return validate_plan(result['schedule'])['run_key']
    return digest({key: result.get(key) for key in ('collected_at', 'query', 'hours')})


@contextmanager
def connection(url):
    if not url:
        raise ValueError('Database connection setting is missing')
    try:
        import psycopg
    except ImportError:
        raise ValueError('Install requirements.txt to use PostgreSQL') from None
    try:
        with psycopg.connect(url, sslmode='verify-full', connect_timeout=15) as db:
            yield db
    except psycopg.Error:
        # Driver errors can contain connection strings or row values.
        raise ValueError('PostgreSQL operation failed; no local fallback was used') from None


def migrate(url):
    paths = sorted((Path(__file__).resolve().parent.parent / 'migrations').glob('[0-9][0-9][0-9]_*.sql'))
    with connection(url) as db:
        db.execute('SELECT pg_advisory_xact_lock(736421)')
        db.execute('CREATE SCHEMA IF NOT EXISTS briefing')
        db.execute('CREATE TABLE IF NOT EXISTS briefing.schema_migrations '
                   '(version integer PRIMARY KEY, checksum text NOT NULL)')
        for path in paths:
            version = int(path.name.split('_')[0])
            sql = path.read_text(encoding='utf-8')
            checksum = hashlib.sha256(sql.encode()).hexdigest()
            row = db.execute('SELECT checksum FROM briefing.schema_migrations WHERE version=%s', (version,)).fetchone()
            if row:
                if row[0] != checksum:
                    raise ValueError('Applied migration checksum differs; create a new migration')
                continue
            db.execute(sql)
            db.execute('INSERT INTO briefing.schema_migrations VALUES (%s, %s)', (version, checksum))


class PostgresStore:
    def __init__(self, url):
        self.url = url

    def save(self, result, subject, body):
        from .__main__ import read_snapshot
        read_snapshot(result)
        if 'schedule' in result:
            raise ValueError('Use the scheduled job entry point to persist scheduled snapshots')
        content_hash = digest([result, subject, body])
        with connection(self.url) as db:
            row = db.execute(
                'INSERT INTO briefing.runs '
                '(id,run_key,trigger,collected_at,query,status,source_results) '
                "VALUES (%s,%s,'manual_snapshot',%s,%s,%s,%s::jsonb) "
                'ON CONFLICT (run_key) DO NOTHING RETURNING id',
                (uuid.uuid4(), snapshot_key(result), result['collected_at'], result['query'],
                 'ready' if result['articles'] else 'empty',
                 json.dumps(dict(states=result['sources'], details=result.get('source_details', {}))))).fetchone()
            if row is None:
                row = db.execute('SELECT id FROM briefing.runs WHERE run_key=%s',
                                 (snapshot_key(result),)).fetchone()
            run_id = row[0]
            db.execute('INSERT INTO briefing.briefings '
                       '(id,run_id,schema_version,payload,content_hash,subject,body) '
                       'VALUES (%s,%s,%s,%s::jsonb,%s,%s,%s) ON CONFLICT (run_id) DO NOTHING',
                       (uuid.uuid4(), run_id, result['schema_version'], json.dumps(result),
                        content_hash, subject, body))
            saved = db.execute('SELECT id,content_hash FROM briefing.briefings WHERE run_id=%s',
                               (run_id,)).fetchone()
            if saved[1] != content_hash:
                raise ValueError('Stored snapshot is immutable; content differs for this run')
            return str(saved[0])

    def load(self, briefing_id):
        with connection(self.url) as db:
            row = db.execute('SELECT payload,subject,body FROM briefing.briefings WHERE id=%s',
                             (briefing_id,)).fetchone()
            if not row:
                raise ValueError('Stored briefing not found')
            return row

    def claim_schedule(self, plan):
        """Return (claim id, None) to the owner or (None, saved briefing) on replay."""
        from .schedule import validate_plan
        validate_plan(plan)
        with connection(self.url) as db:
            row = db.execute(
                'INSERT INTO briefing.runs '
                '(id,run_key,trigger,collected_at,query,status,source_results,schedule) '
                "VALUES (%s,%s,'schedule',now(),%s,'collecting','{}'::jsonb,%s::jsonb) "
                'ON CONFLICT (run_key) DO NOTHING RETURNING id',
                (uuid.uuid4(), plan['run_key'], plan['query'], json.dumps(plan))).fetchone()
            if row:
                return str(row[0]), None
            row = db.execute('SELECT r.status,b.id,b.payload,b.subject,b.body FROM briefing.runs r '
                             'LEFT JOIN briefing.briefings b ON b.run_id=r.id WHERE r.run_key=%s',
                             (plan['run_key'],)).fetchone()
            if row and row[0] in ('ready', 'empty') and row[1] is not None:
                return None, (str(row[1]), row[2], row[3], row[4])
            raise ValueError('Scheduled run already collecting or failed; manual reconciliation required')

    def complete_schedule(self, claim_id, result, subject, body):
        from .__main__ import read_snapshot
        read_snapshot(result)
        plan = result['schedule']
        with connection(self.url) as db:
            row = db.execute('SELECT id FROM briefing.runs '
                             "WHERE id=%s AND run_key=%s AND status='collecting' FOR UPDATE",
                             (claim_id, plan['run_key'])).fetchone()
            if row is None:
                raise ValueError('Scheduled collection claim is not owned by this execution')
            bid = uuid.uuid4()
            db.execute('INSERT INTO briefing.briefings '
                       '(id,run_id,schema_version,payload,content_hash,subject,body) '
                       'VALUES (%s,%s,%s,%s::jsonb,%s,%s,%s)',
                       (bid, claim_id, result['schema_version'], json.dumps(result),
                        digest([result, subject, body]), subject, body))
            db.execute('UPDATE briefing.runs SET status=%s, source_results=%s::jsonb WHERE id=%s',
                       ('ready' if result['articles'] else 'empty',
                        json.dumps(dict(states=result['sources'], details=result.get('source_details', {}))), claim_id))
            return str(bid)

    def fail_schedule(self, claim_id):
        with connection(self.url) as db:
            db.execute("UPDATE briefing.runs SET status='failed' WHERE id=%s AND status='collecting'", (claim_id,))


class PostgresLedger:
    def __init__(self, url, briefing_id, recipient):
        self.url, self.briefing_id, self.recipient = url, briefing_id, recipient.strip()

    def claim(self, key):
        with connection(self.url) as db:
            inserted = db.execute(
                'INSERT INTO briefing.deliveries (delivery_key,briefing_id,recipient,status) '
                "VALUES (%s,%s,%s,'sending') ON CONFLICT DO NOTHING RETURNING delivery_key",
                (key, self.briefing_id, self.recipient)).fetchone()
            if inserted:
                return True
            row = db.execute('SELECT briefing_id,recipient FROM briefing.deliveries WHERE delivery_key=%s',
                             (key,)).fetchone()
            if row is None or str(row[0]) != self.briefing_id or row[1] != self.recipient:
                raise ValueError('Delivery identity conflict; refusing to send')
            return False

    def get(self, key):
        with connection(self.url) as db:
            row = db.execute('SELECT status,message_id FROM briefing.deliveries '
                             'WHERE delivery_key=%s AND briefing_id=%s AND recipient=%s',
                             (key, self.briefing_id, self.recipient)).fetchone()
            return DeliveryResult(*row) if row else None

    def finish(self, key, status, message_id=None):
        if status not in ('sent', 'failed', 'unknown'):
            raise ValueError('Invalid delivery result')
        with connection(self.url) as db:
            row = db.execute('UPDATE briefing.deliveries SET status=%s,message_id=%s,finished_at=now() '
                             "WHERE delivery_key=%s AND briefing_id=%s AND recipient=%s AND status='sending' "
                             'RETURNING delivery_key',
                             (status, message_id, key, self.briefing_id, self.recipient)).fetchone()
            if not row:
                raise ValueError('Delivery status transition rejected')


if __name__ == '__main__':
    import argparse
    from .__main__ import load_dotenv
    parser = argparse.ArgumentParser()
    parser.add_argument('--migrate', action='store_true', required=True)
    parser.parse_args()
    load_dotenv()
    try:
        migrate(os.environ.get('DATABASE_MIGRATION_URL'))
    except ValueError as error:
        parser.exit(1, f'{error}\n')
    print('Database schema is ready')
