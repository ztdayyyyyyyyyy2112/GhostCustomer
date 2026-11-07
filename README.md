# Ghost Customer Prediction

STAT3013 project: early detection of silent customer disengagement in e-commerce. The repository contains a reproducible statistical study and a web demo. The term “ghost customer” is an operational label defined by the team, not a directly observed mental state or proof of churn.

## Current status

The frontend runs with **illustrative mock data**. The dataset, cohort rules, label thresholds, statistical estimates, and trained model are not finalized. Do not present mock values as research results.

## Run the frontend

Requires Node.js 24 and npm. From the repository root:

```bash
cd frontend
cp .env.example .env.local
npm ci
npm run dev
```

On PowerShell, use `Copy-Item .env.example .env.local` instead of `cp` if needed. Open <http://localhost:3000>. The default `NEXT_PUBLIC_API_MODE=mock` needs no backend. Run `npm run lint` and `npm run build` before a PR.

## Repository layout

- `frontend/`: Next.js dashboard and shared API client.
- `backend/`: planned FastAPI application.
- `data/`: data scripts, notebooks, and ignored raw/processed files.
- `ai/`: planned model training and inference.
- `research/`: statistics, regression, and forecasting work.
- `docs/`: research scope, decisions, literature map, evidence register, API contract, team handoff, runbook, and submission checks.
- `reports/`: report draft and writing outlines for the paper and slides. No empirical findings are published yet.

## Working agreements

Start from `develop`, use a `feature/*` branch, and open a PR to `develop`. Include the issue or task ID, changed inputs/outputs, commands run, and any contract changes. Review [CONTRIBUTING.md](CONTRIBUTING.md) before changing shared schemas. Never commit secrets, raw datasets, large processed data, or trained model files.
