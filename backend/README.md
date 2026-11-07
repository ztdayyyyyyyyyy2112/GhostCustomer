# GhostCustomer Backend API

FastAPI application implementing the 7 contract routes defined in [`docs/api_contract.md`](../docs/api_contract.md) (v0.2).

## Features

- **Strict schema conformance**: Pydantic v2 schemas mirroring the frontend TypeScript definitions in `frontend/src/types/api.ts`.
- **CORS enabled**: Pre-configured for `http://localhost:3000` (configurable via `CORS_ORIGINS` environment variable).
- **Research integrity**: In default mode, pending analyses return standardized empty structures, nulls, and explicit notices (`dataset_notice`). If no model artifact exists, `POST /api/predict` returns HTTP 503 (`Prediction model unavailable`). No fabricated scores or p-values are produced.
- **Fixture mode for integration testing**: Setting `ENABLE_DEMO_FIXTURES=1` enables illustrative contract demonstration fixtures to verify full frontend-backend integration before reproducible model weights are trained.

## Setup and Installation

From the repository root:

```bash
pip install -r backend/requirements.txt
```

## Running the API Server

```bash
python -m uvicorn backend.app.main:app --reload --port 8000
```

Open interactive documentation at:
- Swagger UI: <http://localhost:8000/docs>
- ReDoc: <http://localhost:8000/redoc>

## Testing

Run the automated test suite covering all 7 endpoints, CORS, filtering, pagination, and error handling:

```bash
python -m pytest backend/tests -v
```

## Endpoints Summary

| Method | Route | Description |
| --- | --- | --- |
| `GET` | `/` | Root service info and version |
| `GET` | `/health` | Health check endpoint |
| `GET` | `/api/overview` | Overall cohort counts, rates, and date range |
| `GET` | `/api/customers` | Search, filter by status, sort, and paginate customers |
| `GET` | `/api/customers/{id}` | Detailed customer info, pre-T features, and timeline |
| `GET` | `/api/statistics` | Descriptive statistics, hypothesis tests, and estimates |
| `GET` | `/api/forecast` | Weekly cohort disengagement rate forecast and CIs |
| `POST` | `/api/predict` | Customer disengagement risk prediction (pre-T inputs only) |
| `GET` | `/api/model/metrics` | Held-out model evaluation metrics, confusion matrix, calibration |
