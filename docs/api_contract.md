# API contract — draft v0.3

This is Thành's proposal for review by Long, Lâm, and Kiệt. Backend routes are prefixed with `/api`. Responses use JSON, snake_case keys, UTC ISO-8601 timestamps, and `null` when a value cannot be calculated. A score, when available, is a number in `[0, 1]`. `visitorid` is the source identifier; `customer_id` is its string form in the API. Do not expose future label inputs as prediction features.

The frontend reads `NEXT_PUBLIC_API_MODE=mock|real` and `NEXT_PUBLIC_API_URL`. Mock responses are illustrative and must never be cited as analysis. Live statistical endpoints should return empty results or nulls until reproducible output files exist. The customers list and detail responses include `dataset_notice`, so fixture data remains visibly labeled even when served by the real backend.

## Shared objects

`Customer`: `customer_id: string`, `snapshot_date: string` (ISO date), `status: active|ghost|candidate|recovered|inactive|unknown`, `sessions: number|null`, `views: number|null`, `decay: number|null`, `risk_score: number|null`. `risk_score` is the model estimate; `status` is an operational display state and may be unknown. Define the final mapping from labels to display states in the label decision record.

`CustomerWeekly`: `week_start: string` (ISO date), `views: number`, `carts: number`, `purchases: number`, `sessions: number`, `active_days: number`, `phase: baseline|observation|confirmation`.

`Error`: `{"detail":"Human-readable error"}`. Use HTTP 400/422 for invalid input, 404 for unknown customer, 503 for unavailable model or results, and 500 for unexpected failure. Never return a made-up statistic as a fallback.

## Endpoints and examples

### `GET /api/overview`

```json
{"total_customers":5,"active_count":2,"ghost_count":1,"candidate_count":1,"unknown_count":1,"inactive_count":0,"recovered_count":0,"active_rate":0.4,"ghost_rate":0.2,"date_range":{"start":"2026-01-05","end":"2026-02-16"},"dataset_notice":"ILLUSTRATIVE MOCK DATA — not research findings"}
```

Rates use `total_customers` as denominator in this draft; change only with an explicit decision on eligible cohort. If the denominator is zero, return `null` for rates.

### `GET /api/customers?page=1&page_size=20&status=ghost&search=C001&sort=snapshot_date&order=desc`

`page` is one-based; `page_size` is 1–100. `status` and `search` are optional. Allowed sort keys: `snapshot_date`, `sessions`, `views`, `decay`, `risk_score`.

```json
{"items":[{"customer_id":"C001","snapshot_date":"2026-02-16","status":"ghost","sessions":2,"views":4,"decay":0.65,"risk_score":0.73}],"page":1,"page_size":20,"total":1,"dataset_notice":"ILLUSTRATIVE MOCK DATA — not research findings"}
```

### `GET /api/customers/{id}`

Pass `snapshot_date=YYYY-MM-DD` when opening a row from the customer list. One visitor may have multiple dated snapshots; the response must match both `customer_id` and `snapshot_date`. Without the query parameter, the API returns that visitor's latest available snapshot. An unknown ID or unavailable date returns 404; an invalid date returns 422.

```json
{"customer":{"customer_id":"C001","snapshot_date":"2026-02-16","status":"ghost","sessions":2,"views":4,"decay":0.65,"risk_score":0.73},"current_features":{"sessions_4w":2,"views_4w":4,"days_since_last_view":6},"weekly_timeline":[{"week_start":"2026-02-09","views":4,"carts":0,"purchases":0,"sessions":2,"active_days":2,"phase":"observation"}],"status":"ghost","dataset_notice":"ILLUSTRATIVE MOCK DATA — not research findings"}
```

`current_features` contains only data at or before `snapshot_date`. The `confirmation` timeline, if shown for retrospective explanation, is never submitted to prediction.

### `GET /api/statistics`

```json
{"groups":[],"estimates":[],"tests":[],"p_values":[],"cis":[],"assumptions":[],"dataset_notice":"Results unavailable until statistical pipeline runs"}
```

Each published test should include `name`, `hypothesis`, `n`, `statistic`, `p_value`, `effect_size`, `ci_low`, `ci_high`, `method`, and `assumptions`; nulls are allowed when inapplicable. The arrays stay empty before analysis, not populated with demo p-values.

For charts and summary tables, each `groups[]` item proposes `name`, `metric`, `unit`, `n`, `mean`, `median`, `q1`, `q3`, `min`, `max`, and `histogram: [{lower, upper, count}]`. Each `estimates[]` item proposes `name`, `n`, `estimate`, `ci_low`, `ci_high`, `method`, and `unit`. All values must come from the same reproducible analysis. These shapes remain open for review by Lâm and Long.

### `GET /api/forecast`

```json
{"history":[],"fitted":[],"predictions":[],"lower_ci":[],"upper_ci":[],"method":null,"mae":null,"rmse":null,"smape":null,"train_end":null,"unit":null,"series_length":null,"dataset_notice":"Forecast unavailable until time-series analysis runs"}
```

Each history/prediction point is `{ "date": "2026-02-16", "value": 0.2 }`. These values are ghost rates in `[0, 1]`; interval bounds should also stay within the valid rate range. CI arrays have matching dates and lengths when present. Do not plot a forecast over an unsupported horizon.

`fitted[]` is optional and contains in-sample fitted values only. `train_end` marks the last training date; `unit` is `day` or `week`; `series_length` counts usable observations. The frontend draws observed, fitted, and future series separately without connecting unrelated periods.

### `POST /api/predict`

Request exactly one of `customer_id` with `snapshot_date`, or a non-empty validated `features` object (pre-T fields only). Extra top-level fields are rejected. The approved feature allowlist and preprocessing version still need to be supplied by Kiệt:

```json
{"customer_id":"C001","snapshot_date":"2026-02-16"}
```

Response:

```json
{"score":0.73,"risk_label":"mock","top_factors":[],"model_version":"mock-v0","dataset_notice":"ILLUSTRATIVE MOCK PREDICTION"}
```

When no model is loaded, return HTTP 503 with `{"detail":"Prediction model unavailable"}`. `risk_label` threshold must come from validation data, not the test set.

For a real model, `ai/inference/runtime.py` exports `predict(payload: dict) -> dict`; the backend validates the return value as `PredictResponse`, including `score` in `[0, 1]`. The runtime owns model loading and pre-T feature derivation. A saved `model.pkl` without this runtime does not enable inference. See `docs/integration_handoff.md`.

Mock mode uses the selected customer's illustrative `risk_score` for I/O demonstration and returns no fabricated SHAP factors. It returns 404 for an unknown ID and 422 for an unknown status or mismatched snapshot.

### `GET /api/model/metrics`

```json
{"models":[],"comparison":[],"evaluation_context":null,"confusion_matrix":null,"calibration":[],"dataset_notice":"Metrics unavailable until held-out evaluation runs"}
```

Every reported metric needs model version, split, support, class prevalence, and threshold where relevant. Do not fill empty arrays with fabricated scores.

Each `models[]` row proposes `name`, `model_version`, `split`, `support`, `prevalence`, `threshold`, `precision`, `recall`, `f1`, `roc_auc`, `pr_auc`, and `brier`. Values that cannot be calculated are `null`. Each `calibration[]` bin proposes `mean_predicted`, `observed_rate`, and `n`. `confusion_matrix` is `[[TN, FP], [FN, TP]]`. When a matrix or calibration is present, `evaluation_context` must identify its `model_version`, `split`, and `threshold`; otherwise it is `null`. The frontend suppresses those sections without context to avoid attributing them to the wrong model or data split.

## Review questions

- Lâm: Are source IDs, date windows, statuses, and null rules consistent with the processed data dictionary?
- Long: Can Pydantic schemas and all seven routes implement these examples and error codes?
- Kiệt: Does prediction input exclude IDs/future fields from model features, and does output match inference packaging?
