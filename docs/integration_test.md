# Frontend–backend integration matrix

Status: **not run**. The backend has not been provided in this repository. Complete this matrix with a date, backend commit, dataset version, and tester when the API is available. Contract source: `docs/api_contract.md`.

| Endpoint | Success case | Error and boundary case | Evidence |
| --- | --- | --- | --- |
| `GET /api/overview` | Counts, rates, date range and dataset notice match result files | Empty cohort returns null rates, not NaN | Pending |
| `GET /api/customers` | Search, status, sort, page and total match UI | Page outside range and invalid page size handled | Pending |
| `GET /api/customers/{id}` | Current features and weekly timeline have valid phases | Unknown ID returns 404; future values absent from `current_features` | Pending |
| `GET /api/statistics` | N, estimate, CI, p, effect and assumptions match notebook | No completed analysis returns empty arrays | Pending |
| `GET /api/forecast` | History, fitted, predictions and CI align by date | Missing/short series returns empty values or clear error | Pending |
| `POST /api/predict` | Score is 0–1, version and factors match inference | Unknown customer, invalid features and unavailable model return 404/422/503 | Pending |
| `GET /api/model/metrics` | Test support, prevalence, threshold and metrics match saved evaluation | Missing model results return empty arrays | Pending |

Additional checks: frontend error and loading states, CORS from the frontend origin, UTF-8 text, ISO dates, null handling, mobile table scrolling, and no secrets or raw data in responses. Record screenshots or response files only after using the real backend; never relabel mock evidence as research output.
