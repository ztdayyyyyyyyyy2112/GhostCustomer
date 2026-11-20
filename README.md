# Ghost Customer Prediction

STAT3013 project: early detection of silent customer disengagement in e-commerce. The repository contains a reproducible statistical study and a web demo. The term “ghost customer” is an operational label defined by the team, not a directly observed mental state or proof of churn.

## Current status

The repository now contains a reproducible **local real-data demo**: data pipeline, descriptive and inferential statistics, OLS and logistic regression, a short-series naive forecast, model evaluation, saved-model inference, seven API routes, and a Next.js dashboard. On 20 November 2026 the integrated real-data check passed locally. Raw/processed visitor data and the trained model stay out of Git, so a new machine must rebuild them. The 4+2+2 cohort and Ghost label remain proposed research decisions; see `docs/decision_log.md` and the observation-only ablation before making performance claims.

## Rebuild the real-data demo

Save the Retailrocket Kaggle v2 `events.csv` at `data/raw/events.csv`. Its SHA-256 must match `data/config/pipeline.json`. In a Python 3.12+ virtual environment, from the repository root:

```bash
python -m pip install -r requirements-defense.txt
python -m scripts.prepare_real_demo
```

This command rebuilds the ignored processed tables and model, tracked aggregate research results, and then checks all seven real API routes. It takes several minutes. With already verified processed tables, use `python -m scripts.prepare_real_demo --from-processed`. See `docs/runbook.md` for the exact study limitations and frontend setup.

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

Check the status and shape of research handoff files without modifying them:

```bash
python scripts/check_integration_artifacts.py
```

After rebuilding local artifacts, use `--require-complete` to fail on missing files. This checks structure and does not replace scientific review.

Swagger API documentation is available at <http://localhost:8000/docs>. To connect the frontend in real mode, set `NEXT_PUBLIC_API_MODE=real` and `NEXT_PUBLIC_API_URL=http://localhost:8000` in `frontend/.env.local`.

For a full-stack interface check before research outputs arrive, start the backend with `ENABLE_DEMO_FIXTURES=1` (PowerShell: `$env:ENABLE_DEMO_FIXTURES='1'`). Fixture responses are visibly marked as illustrative. Remove the variable and restart the backend for normal empty/unavailable behavior. Rebuild the frontend after changing `NEXT_PUBLIC_*` values for a production run.

## Repository layout

- `frontend/`: Next.js dashboard and shared API client.
- `backend/`: FastAPI application implementing the contract in `docs/api_contract.md`.
- `data/`: data scripts, notebooks, and ignored raw/processed files.
- `ai/`: model training, evaluation, saved-model inference and model card.
- `research/`: statistics, regression, and forecasting work.
- `docs/`: research scope, decisions, literature map, evidence register, API contract, team handoff, runbook, and submission checks.
- `reports/`: report and presentation drafts tied to reproducible evidence; review them before submission.

## Working agreements

Start from `develop`, use a `feature/*` branch, and open a PR to `develop`. Include the issue or task ID, changed inputs/outputs, commands run, and any contract changes. Review [CONTRIBUTING.md](CONTRIBUTING.md) before changing shared schemas. Never commit secrets, raw datasets, large processed data, or trained model files.
