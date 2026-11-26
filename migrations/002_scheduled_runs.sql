ALTER TABLE briefing.runs DROP CONSTRAINT runs_status_check;
ALTER TABLE briefing.runs ADD CONSTRAINT runs_status_check
    CHECK (status IN ('collecting', 'ready', 'empty', 'failed'));
ALTER TABLE briefing.runs ADD COLUMN schedule jsonb;
