PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS customer_snapshot (
    visitorid TEXT NOT NULL,
    snapshot_date TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('active','ghost','candidate','recovered','inactive','unknown')),
    sessions INTEGER CHECK(sessions >= 0),
    views INTEGER CHECK(views >= 0),
    decay REAL,
    risk_score REAL CHECK(risk_score BETWEEN 0 AND 1),
    current_features TEXT NOT NULL CHECK(json_valid(current_features)),
    dataset_notice TEXT NOT NULL,
    PRIMARY KEY(visitorid, snapshot_date)
);
CREATE INDEX IF NOT EXISTS ix_snapshot_status_date ON customer_snapshot(status,snapshot_date);
CREATE TABLE IF NOT EXISTS customer_weekly (
    visitorid TEXT NOT NULL,
    snapshot_date TEXT NOT NULL,
    week_start TEXT NOT NULL,
    phase TEXT NOT NULL CHECK(phase IN ('baseline','observation','confirmation')),
    views INTEGER NOT NULL CHECK(views>=0),
    carts INTEGER NOT NULL CHECK(carts>=0),
    purchases INTEGER NOT NULL CHECK(purchases>=0),
    sessions INTEGER NOT NULL CHECK(sessions>=0),
    active_days INTEGER NOT NULL CHECK(active_days BETWEEN 0 AND 7),
    PRIMARY KEY(visitorid,snapshot_date,week_start),
    FOREIGN KEY(visitorid,snapshot_date) REFERENCES customer_snapshot(visitorid,snapshot_date) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS metrics (
    artifact_name TEXT PRIMARY KEY,
    payload TEXT NOT NULL CHECK(json_valid(payload)),
    artifact_version TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS predictions (
    id INTEGER PRIMARY KEY,
    visitorid TEXT NOT NULL,
    snapshot_date TEXT NOT NULL,
    score REAL NOT NULL CHECK(score BETWEEN 0 AND 1),
    risk_label TEXT NOT NULL,
    model_version TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(visitorid,snapshot_date) REFERENCES customer_snapshot(visitorid,snapshot_date) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS ix_predictions_snapshot ON predictions(visitorid,snapshot_date);
CREATE TABLE IF NOT EXISTS provenance (key TEXT PRIMARY KEY, value TEXT NOT NULL);
