CREATE SCHEMA IF NOT EXISTS briefing;
CREATE TABLE briefing.runs (
    id uuid PRIMARY KEY,
    run_key text NOT NULL UNIQUE,
    trigger text NOT NULL CHECK (trigger IN ('manual_snapshot', 'schedule')),
    collected_at timestamptz NOT NULL,
    query text NOT NULL,
    status text NOT NULL CHECK (status IN ('ready', 'empty')),
    source_results jsonb NOT NULL
);
CREATE TABLE briefing.briefings (
    id uuid PRIMARY KEY,
    run_id uuid NOT NULL UNIQUE REFERENCES briefing.runs(id),
    schema_version integer NOT NULL,
    payload jsonb NOT NULL,
    content_hash text NOT NULL,
    subject text NOT NULL,
    body text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE briefing.deliveries (
    delivery_key text PRIMARY KEY,
    briefing_id uuid NOT NULL REFERENCES briefing.briefings(id),
    recipient text NOT NULL,
    status text NOT NULL CHECK (status IN ('sending', 'sent', 'failed', 'unknown')),
    message_id text,
    attempted_at timestamptz NOT NULL DEFAULT now(),
    finished_at timestamptz,
    UNIQUE (briefing_id, recipient)
);
