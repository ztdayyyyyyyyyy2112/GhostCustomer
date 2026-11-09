# Ghost Customer Prediction

STAT3013 project: early detection of silent customer disengagement in e-commerce. The repository contains a reproducible statistical study and a web demo. The term “ghost customer” is an operational label defined by the team, not a directly observed mental state or proof of churn.

## Current status

The frontend runs with **illustrative mock data** or connected to the FastAPI backend. The dataset, cohort rules, label thresholds, statistical estimates, and trained model are not finalized. The real-data file and inference interface is documented in `docs/integration_handoff.md`. Do not present mock values as research results.

## Run the frontend

Requires Node.js 24 and npm. From the repository root:

```bash
cd frontend
cp .env.example .env.local
npm ci
npm run dev
```

On PowerShell, use `Copy-Item .env.example .env.local` instead of `cp` if needed. Open <http://localhost:3000>. The default `NEXT_PUBLIC_API_MODE=mock` needs no backend. Run `npm run lint` and `npm run build` before a PR.

## Run the backend

Requires Python 3.10+. From the repository root:

```bash
pip install -r backend/requirements.txt
python -m uvicorn backend.app.main:app --reload --port 8000
```

Run backend unit and integration tests:

```bash
python -m pytest backend/tests -v
```

Swagger API documentation is available at <http://localhost:8000/docs>. To connect the frontend in real mode, set `NEXT_PUBLIC_API_MODE=real` and `NEXT_PUBLIC_API_URL=http://localhost:8000` in `frontend/.env.local`.

For a full-stack interface check before research outputs arrive, start the backend with `ENABLE_DEMO_FIXTURES=1` (PowerShell: `$env:ENABLE_DEMO_FIXTURES='1'`). Fixture responses are visibly marked as illustrative. Remove the variable and restart the backend for normal empty/unavailable behavior. Rebuild the frontend after changing `NEXT_PUBLIC_*` values for a production run.

## Repository layout

- `frontend/`: Next.js dashboard and shared API client.
- `backend/`: FastAPI application implementing the contract in `docs/api_contract.md`.
- `data/`: data scripts, notebooks, and ignored raw/processed files.
- `ai/`: planned model training and inference.
- `research/`: statistics, regression, and forecasting work.
- `docs/`: research scope, decisions, literature map, evidence register, API contract, team handoff, runbook, and submission checks.
- `reports/`: report draft and writing outlines for the paper and slides. No empirical findings are published yet.

## Working agreements

Start from `develop`, use a `feature/*` branch, and open a PR to `develop`. Include the issue or task ID, changed inputs/outputs, commands run, and any contract changes. Review [CONTRIBUTING.md](CONTRIBUTING.md) before changing shared schemas. Never commit secrets, raw datasets, large processed data, or trained model files.
