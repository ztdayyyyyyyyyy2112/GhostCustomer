# API contract — draft v0.1

This is Thành's proposal for review by Long, Lâm, and Kiệt. Backend routes are prefixed with `/api`. Responses use JSON, snake_case keys, UTC ISO-8601 timestamps, and `null` when a value cannot be calculated. A score, when available, is a number in `[0, 1]`. `visitorid` is the source identifier; `customer_id` is its string form in the API. Do not expose future label inputs as prediction features.

The frontend reads `NEXT_PUBLIC_API_MODE=mock|real` and `NEXT_PUBLIC_API_URL`. Mock responses are illustrative and must never be cited as analysis. Live statistical endpoints should return empty results or nulls until reproducible output files exist.

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
{"items":[{"customer_id":"C001","snapshot_date":"2026-02-16","status":"ghost","sessions":2,"views":4,"decay":0.65,"risk_score":0.73}],"page":1,"page_size":20,"total":1}
```

### `GET /api/customers/{id}`

```json
{"customer":{"customer_id":"C001","snapshot_date":"2026-02-16","status":"ghost","sessions":2,"views":4,"decay":0.65,"risk_score":0.73},"current_features":{"sessions_4w":2,"views_4w":4,"days_since_last_view":6},"weekly_timeline":[{"week_start":"2026-02-09","views":4,"carts":0,"purchases":0,"sessions":2,"active_days":2,"phase":"observation"}],"status":"ghost"}
```

`current_features` contains only data at or before `snapshot_date`. The `confirmation` timeline, if shown for retrospective explanation, is never submitted to prediction.

### `GET /api/statistics`

```json
{"groups":[],"estimates":[],"tests":[],"p_values":[],"cis":[],"assumptions":[],"dataset_notice":"Results unavailable until statistical pipeline runs"}
```

Each published test should include `name`, `hypothesis`, `n`, `statistic`, `p_value`, `effect_size`, `ci_low`, `ci_high`, `method`, and `assumptions`; nulls are allowed when inapplicable. The arrays stay empty before analysis, not populated with demo p-values.

### `GET /api/forecast`

```json
{"history":[],"predictions":[],"lower_ci":[],"upper_ci":[],"method":null,"mae":null,"rmse":null,"smape":null,"dataset_notice":"Forecast unavailable until time-series analysis runs"}
```

Each history/prediction point is `{ "date": "2026-02-16", "value": 0.2 }`. CI arrays have matching dates and lengths when present. Do not plot a forecast over an unsupported horizon.

### `POST /api/predict`

Request either `customer_id` with `snapshot_date`, or a validated `features` object (pre-T fields only):

```json
{"customer_id":"C001","snapshot_date":"2026-02-16"}
```

Response:

```json
{"score":0.73,"risk_label":"high","top_factors":[{"feature":"sessions_4w","contribution":0.18}],"model_version":"mock-v0","dataset_notice":"ILLUSTRATIVE MOCK PREDICTION"}
```

When no model is loaded, return HTTP 503 with `{"detail":"Prediction model unavailable"}`. `risk_label` threshold must come from validation data, not the test set.

### `GET /api/model/metrics`

```json
{"models":[],"comparison":[],"confusion_matrix":null,"calibration":[],"dataset_notice":"Metrics unavailable until held-out evaluation runs"}
```

Every reported metric needs model version, split, support, class prevalence, and threshold where relevant. Do not fill empty arrays with fabricated scores.

## Review questions

- Lâm: Are source IDs, date windows, statuses, and null rules consistent with the processed data dictionary?
- Long: Can Pydantic schemas and all seven routes implement these examples and error codes?
- Kiệt: Does prediction input exclude IDs/future fields from model features, and does output match inference packaging?
