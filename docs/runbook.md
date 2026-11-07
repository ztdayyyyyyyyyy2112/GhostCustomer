# Runbook for Ghost Customer Prediction

## Current state

The Next.js frontend is runnable with illustrative mock data. The backend, processed dataset, statistical results, forecast, and trained inference artifact are still required from their owners. The full-report introduction and methods are a pre-data draft, not findings. Do not use mock scores or screens as evidence of model performance.

## Start the frontend on a fresh machine

Use Node.js 24 and npm. Clone the repository, then from its root:

```bash
cd frontend
npm ci
```

Copy `.env.example` to `.env.local` (`Copy-Item .env.example .env.local` in PowerShell). Keep `NEXT_PUBLIC_API_MODE=mock`, then run `npm run dev` and open <http://localhost:3000>. Check `/dashboard`, `/customers`, `/customers/C001`, `/statistics`, `/forecast`, `/predict`, and `/models`. The mock C001 prediction is illustrative; C005 should report insufficient data.

## Quality checks

From `frontend/`, run `npm run lint` and `npm run build`. GitHub Actions runs both checks for frontend changes in pull requests to `develop` or `main`. A successful frontend build does not validate backend responses or research results.

## Connect the real backend

1. Agree on `docs/api_contract.md` with the data, backend, and AI owners. The current contract is a draft; record accepted schema changes in a PR.
2. Start the backend using its own README once implemented. Confirm `/docs` and the seven `/api` endpoints.
3. In `frontend/.env.local`, set `NEXT_PUBLIC_API_MODE=real` and `NEXT_PUBLIC_API_URL=http://localhost:8000`. Restart Next.js after changing `NEXT_PUBLIC_*` values.
4. Run the cases in `docs/integration_test.md`. Check the browser console, server logs, response shapes, 404/422/503 behavior, CORS, pagination, and null values.
5. Compare every published metric, plot, model version, and sample count with the reproducible notebook or result file. Keep unavailable sections empty rather than substituting mock data.

## Data and research handoff

Lâm supplies dataset provenance/license, data dictionary, cohort coverage, label sensitivity, and processed data under `data/processed/`. Large raw and processed files are ignored by Git. Long supplies statistical result tables, forecast output, and FastAPI routes. Kiệt supplies the inference package, held-out model evaluation, calibration, and model card. The leader records decisions in `docs/decision_log.md` before finalizing thresholds or claims.

Use only events at or before snapshot T as features. Keep future confirmation events in a separate timeline. Preserve `unknown` when the future horizon is not fully observable. Train/validation/test splits must respect time and repeated visitors. Never treat observational associations as causal evidence.

## Demo and final handoff

The demo path is Overview → Customer List → Customer Detail → Statistical Insights → Forecast → Prediction → Model Metrics. In mock mode, introduce it as a technical interface demo. For the final demo, use `real` mode and verify all numbers against result files. Check the final report, IEEE paper, slides, video, source code, evidence screenshots, and links using `docs/submission_checklist.md`.
