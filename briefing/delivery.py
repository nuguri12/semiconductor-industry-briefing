"""Offline-safe delivery state with durable duplicate suppression."""

import sqlite3
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path


class DeliveryUnknown(Exception):
    """The remote service may have accepted the message."""


@dataclass(frozen=True)
class DeliveryResult:
    status: str
    message_id: str | None = None


class DeliveryLedger:
    def __init__(self, path):
        self.path = str(path)
        with closing(self._connect()) as db, db:
            db.execute("""CREATE TABLE IF NOT EXISTS deliveries (
                delivery_key TEXT PRIMARY KEY,
                status TEXT NOT NULL,
                message_id TEXT
            )""")

    def _connect(self):
        db = sqlite3.connect(self.path, timeout=10)
        db.execute("PRAGMA busy_timeout = 10000")
        return db

    def claim(self, key):
        with closing(self._connect()) as db, db:
            cursor = db.execute(
                "INSERT INTO deliveries(delivery_key,status) VALUES(?, 'sending') ON CONFLICT DO NOTHING",
                (key,),
            )
            return cursor.rowcount == 1

    def finish(self, key, status, message_id=None):
        with closing(self._connect()) as db, db:
            db.execute("UPDATE deliveries SET status=?, message_id=? WHERE delivery_key=? AND status='sending'",
                       (status, message_id, key))

    def get(self, key):
        with closing(self._connect()) as db:
            row = db.execute("SELECT status,message_id FROM deliveries WHERE delivery_key=?", (key,)).fetchone()
            return DeliveryResult(*row) if row else None


def dispatch(ledger, key, message, sender, *, dry_run=False):
    if dry_run:
        return DeliveryResult("dry_run")
    if not ledger.claim(key):
        return ledger.get(key)
    try:
        message_id = sender(message)
    except DeliveryUnknown:
        ledger.finish(key, "unknown")
        return ledger.get(key)
    except Exception:
        ledger.finish(key, "failed")
        return ledger.get(key)
    ledger.finish(key, "sent", message_id)
    return ledger.get(key)
