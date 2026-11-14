# Real-data integration handoff (draft v0.4)

Updated 14 November 2026. The frontend and FastAPI backend run together. Lâm's proposed Retailrocket `overview.json`, `customers.json`, customer detail files, and descriptive `research/statistics/results.json` are now generated locally under `data/processed/` (statistics also has a small reviewed-shape JSON in Git). Outputs remain preliminary pending owner review; this handoff does not approve the cohort or label.

## Artifact locations and owners

| Owner | Input to hand over | Consumer and minimum check |
| --- | --- | --- |
| Lâm | `data/processed/overview.json` | `/api/overview`; exact `OverviewResponse` shape in `docs/api_contract.md`, with counts/rates based on the approved cohort and a source notice. |
| Lâm | `data/processed/customers.json` | `/api/customers`; JSON array of `Customer` rows, one per `(customer_id, snapshot_date)`. Keep duplicate visitor IDs across dates; do not duplicate the same pair. Dates are ISO `YYYY-MM-DD`. |
| Lâm | `data/processed/customer_details/YYYY-MM-DD/<sha256(customer_id UTF-8)>.json` | `/api/customers/{id}?snapshot_date=YYYY-MM-DD`; each file is a complete `CustomerDetailResponse`, including matching `customer`, `status`, `current_features`, `weekly_timeline`, and `dataset_notice`. The filename is the lowercase 64-character SHA-256 hex digest of the UTF-8 customer ID. |
| Long | `research/statistics/results.json` | `/api/statistics`; `StatisticsResponse` shape, with N, method, assumptions, CIs and effect sizes tied to E-03/E-04/E-05. |
| Long | `research/forecasting/results.json` | `/api/forecast`; `ForecastResponse` shape, dated observed/fitted/future points and holdout errors tied to E-06. |
| Kiệt | `ai/evaluation/metrics.json` | `/api/model/metrics`; `ModelMetricsResponse` shape, evaluation context, class support, prevalence, threshold, confusion matrix and calibration tied to E-07. |
| Kiệt + Long | `ai/inference/runtime.py` and model artifacts outside Git | `/api/predict`; export `predict(payload: dict) -> dict`. The backend passes exactly one of `{customer_id, snapshot_date}` or `{features}` and validates the returned dictionary as `PredictResponse`. See behavior below. |

`data/raw/*`, `data/processed/*`, model binaries, secrets, and local `.env*` are ignored by Git. Share them by an agreed private data path with version/hash and a regeneration command. Small reviewed research result JSON files may be committed with their generating scripts and evidence record.

## Snapshot and inference behavior

- A customer row represents a visitor at a dated snapshot, not an identified account. The list link passes `snapshot_date`; omitting it returns the latest available date for the visitor. Unknown ID/date returns 404; invalid date returns 422.
- Without a detail file, the API returns the selected summary with empty `current_features` and `weekly_timeline` and an unavailable notice. It does not invent `sessions_4w` from a summary whose window is not known.
- The inference runtime must derive any ID-based features from events at or before the submitted snapshot. It must reject unknown IDs and invalid or unavailable snapshots. Do not accept confirmation events, future labels, or free-form feature names until Kiệt records the final feature allowlist and preprocessing version.
- `predict` returns `score` in `[0,1]`, `risk_label`, `top_factors`, `model_version`, and `dataset_notice`. Raise `LookupError` for an unknown snapshot and `ValueError` for invalid input; the API maps these to 404/422. A missing runtime or malformed response yields 503. The runtime may load a trained model internally; merely adding `model.pkl` does not activate inference.
- Fixture mode (`ENABLE_DEMO_FIXTURES=1`) is for end-to-end interface checks only and visibly says mock. Normal mode returns empty/unavailable responses until approved outputs exist.

## Recheck when each owner hands over work

1. Record D-01–D-07 decisions and link E-01–E-10 evidence in `docs/evidence_register.md`. Compare output hashes and row counts with the owner's reproducible pipeline.
2. From repo root, run `python scripts/check_integration_artifacts.py` to see missing or malformed inputs. When all owners have delivered, run it with `--require-complete`; that mode must exit successfully before final demo. This is a structural check, not approval of scientific methods or model performance.
3. From repo root, run `python -m pytest backend/tests -q`. From `frontend/`, run `npm run lint` and build with `NEXT_PUBLIC_API_MODE=real` plus `NEXT_PUBLIC_API_URL=http://localhost:8000`. Restart/rebuild after changing `NEXT_PUBLIC_*` values.
4. Start `python -m uvicorn backend.app.main:app --port 8000` and the frontend on port 3000. Visit all seven routes in `docs/runbook.md`; check the browser console, CORS, 404/422/503 cases, nulls, date selection, and mobile layout.
5. For each non-empty API section, compare a real response and a screenshot to the exact source artifact. Keep the model, report, paper, slides, and demo on the same cohort/window/label/version. Do not publish results from fixture mode.

Current limits: generated customer and descriptive artifacts use a proposed cohort/label and are not approved findings. Hypothesis tests/CIs, forecasting results, saved model evaluation, and real inference runtime remain outstanding with their owners. The checked customer/detail artifacts pass the structural checker; scientific approval and model inference remain outstanding.
