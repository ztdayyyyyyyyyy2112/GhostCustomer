# BE-03 SQLite storage design

SQLite stores processed snapshots, per-snapshot weekly timelines, result metadata and prediction logs. Primary keys retain (visitorid, snapshot_date); visitorid is mapped explicitly to customer_id at the API boundary. Snapshot-dependent timeline phases cannot be represented by a visitor/week key alone. Foreign keys prevent orphaned rows; replacements are transactional and invalidate metrics/predictions.

Use `initialize(Path('data/processed/customer_cache.sqlite3'))` then `CustomerRepository(path)`. Keep the DB under the already ignored data/processed directory. The repository supports exact/latest detail lookup, status/search and deterministic pagination. It accepts current API DTOs and preserves null risk scores. It does not generate features, labels or scores, or establish scientific validity of a supplied feature map.

The existing API still reads the agreed JSON artifacts. BE-04 will import validated processed inputs and can export those same JSON files; changing live API storage is a separate integration decision. This branch introduces no frontend or API contract change.

Validation: `python -m pytest backend/tests -q`. New tests cover two snapshots per visitor, filtering, literal SQL-like search, invalid dates/counts/nonfinite values, duplicate rejection and transaction rollback. Inputs are synthetic fixtures only. No dataset or database is committed. Raw event tables remain outside application storage.
