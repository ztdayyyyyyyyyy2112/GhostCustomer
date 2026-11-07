# Frontend–backend integration matrix

Status: **Backend foundation verified (8 November 2026)**. The FastAPI backend is implemented in `backend/app` matching `docs/api_contract.md` v0.2. All 7 endpoints are verified via automated integration tests (`backend/tests/test_api.py`, 12 passed), testing default empty/unavailable behavior (preventing fabricated statistics) and demo fixture validation.

| Endpoint | Success case | Error and boundary case | Evidence |
| --- | --- | --- | --- |
| `GET /api/overview` | Total counts, active/ghost rates, date range, notice | Empty cohort returns 0 counts and null rates | Verified in `test_api.py::test_overview_*` |
| `GET /api/customers` | Search, status filter, sorting, pagination (page, page_size) | Page < 1 or page_size > 100 returns 422 | Verified in `test_api.py::test_customers_*` |
| `GET /api/customers/{id}` | Pre-T features (`sessions_4w`, `views_4w`) and timeline phases | Unknown ID returns 404 with human-readable detail | Verified in `test_api.py::test_customer_detail` |
| `GET /api/statistics` | Structured groups, estimates, tests, p-values | Pending analysis returns empty arrays + notice | Verified in `test_api.py::test_statistics_endpoint` |
| `GET /api/forecast` | Weekly series point format, CIs, evaluation metrics | Pending series returns empty arrays + notice | Verified in `test_api.py::test_forecast_endpoint` |
| `POST /api/predict` | Valid customer returns score, version, notice | Missing model returns 503; unknown ID 404; invalid payload 422 | Verified in `test_api.py::test_predict_*` |
| `GET /api/model/metrics` | Model comparison, evaluation context, confusion matrix | Pending evaluation returns empty arrays + notice | Verified in `test_api.py::test_model_metrics_endpoint` |

Additional verified checks: CORS preflight from `http://localhost:3000`, 422 RequestValidationError detail formatting, ISO dates, null handling. Integration test execution command: `python -m pytest backend/tests -v`.
