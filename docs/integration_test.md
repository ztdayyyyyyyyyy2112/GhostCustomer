# Frontend–backend integration matrix

Status: **Backend foundation and frontend HTTP smoke verified (9 November 2026)**. The FastAPI backend implements draft `docs/api_contract.md` v0.3. The backend suite passes 16 tests, and all seven frontend pages return HTTP 200 with `NEXT_PUBLIC_API_MODE=real` against fixture and empty-state backend modes. This does not validate research results or a trained inference artifact.

| Endpoint | Success case | Error and boundary case | Evidence |
| --- | --- | --- | --- |
| `GET /api/overview` | Total counts, active/ghost rates, date range, notice | Empty cohort returns 0 counts and null rates | Verified in `test_api.py::test_overview_*` |
| `GET /api/customers` | Search, status filter, sorting, pagination (page, page_size), and visible source notice | Page < 1 or page_size > 100 returns 422; invalid processed artifact returns 503 instead of mock data | Verified in `test_api.py::test_customers_*` and `test_invalid_processed_customer_artifact_does_not_fall_back_to_mock` |
| `GET /api/customers/{id}` | Fixture pre-T features and timeline phases; selected processed detail artifact when present; list link passes `snapshot_date` so a repeated visitor opens the selected row | Unknown ID/date returns 404; invalid date returns 422; missing detail artifact keeps features/timeline empty | Verified in `test_api.py::test_customer_detail` and `test_customer_detail_selects_the_requested_snapshot` |
| `GET /api/statistics` | Structured groups, estimates, tests, p-values | Pending analysis returns empty arrays + notice | Verified in `test_api.py::test_statistics_endpoint` |
| `GET /api/forecast` | Weekly series point format, CIs, evaluation metrics | Pending series returns empty arrays + notice | Verified in `test_api.py::test_forecast_endpoint` |
| `POST /api/predict` | Fixture returns score, version, notice; optional real runtime output is schema-checked | Missing runtime returns 503; unknown ID 404; invalid payload 422; malformed runtime score returns 503 | Verified in `test_api.py::test_predict_*` and `test_real_inference_runtime_contract` |
| `GET /api/model/metrics` | Model comparison, evaluation context, confusion matrix | Pending evaluation returns empty arrays + notice | Verified in `test_api.py::test_model_metrics_endpoint` |

Additional verified checks: CORS preflight from `http://localhost:3000`, 422 RequestValidationError detail formatting, ISO dates, null handling, fixture labeling on customer screens, and 503 for malformed research artifacts. Integration test execution command: `python -m pytest backend/tests -q`. Full browser interaction, actual processed research artifacts, and real model inference still require their owners' outputs.
