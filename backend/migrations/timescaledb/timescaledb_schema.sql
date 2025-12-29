-- Bridge Lite Sprint 3: TimescaleDB schema for audit log history
-- Follows docs/02_components/bridge_lite/architecture/bridge_lite_sprint3_spec.md#5-audit-log-etl

CREATE EXTENSION IF NOT EXISTS timescaledb;

CREATE TABLE IF NOT EXISTS audit_logs_ts (
    time TIMESTAMPTZ NOT NULL,
    log_id INTEGER,
    event_type VARCHAR(100),
    intent_id UUID,
    actor VARCHAR(100),
    bridge_type VARCHAR(100),
    status_from VARCHAR(50),
    status_to VARCHAR(50),
    payload JSONB,
    duration_ms INTEGER,
    success BOOLEAN
);

SELECT create_hypertable('audit_logs_ts', 'time', if_not_exists => TRUE);

CREATE INDEX IF NOT EXISTS idx_audit_logs_ts_intent_id ON audit_logs_ts (intent_id, time DESC);
CREATE INDEX IF NOT EXISTS idx_audit_logs_ts_event_type ON audit_logs_ts (event_type, time DESC);
CREATE INDEX IF NOT EXISTS idx_audit_logs_ts_actor ON audit_logs_ts (actor, time DESC);

CREATE MATERIALIZED VIEW IF NOT EXISTS audit_logs_hourly
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 hour', time) AS bucket,
    event_type,
    actor,
    COUNT(*) AS event_count,
    AVG(duration_ms) AS avg_duration_ms,
    SUM(CASE WHEN success THEN 1 ELSE 0 END) AS success_count,
    SUM(CASE WHEN NOT success THEN 1 ELSE 0 END) AS failure_count
FROM audit_logs_ts
GROUP BY bucket, event_type, actor;

SELECT add_continuous_aggregate_policy(
    'audit_logs_hourly',
    start_offset => INTERVAL '2 hours',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour'
);

SELECT add_retention_policy('audit_logs_ts', INTERVAL '90 days');
