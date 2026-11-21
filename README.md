# Ghost Customer Prediction

STAT3013 project: early detection of silent customer disengagement in e-commerce. The repository contains a reproducible statistical study and a web demo. The term “ghost customer” is an operational label defined by the team, not a directly observed mental state or proof of churn.

## Current status

The repository now contains a reproducible **local real-data demo**: data pipeline, descriptive and inferential statistics, OLS and logistic regression, a short-series naive forecast, model evaluation, saved-model inference, seven API routes, and a Next.js dashboard. On 20 November 2026 the integrated real-data check passed locally. Raw/processed visitor data and the trained model stay out of Git, so a new machine must rebuild them. The 4+2+2 cohort and Ghost label remain proposed research decisions; see `docs/decision_log.md` and the observation-only ablation before making performance claims.

## Run the complete project locally (Windows PowerShell)

This is the **real-data** path for a personal demo machine. You need Git, Python 3.12 or newer, Node.js 24 with npm, and the Retailrocket Kaggle v2 `events.csv`. The raw data, processed visitor files and trained model are deliberately absent from Git. Run all commands from the repository root unless a step says otherwise. Use two terminals for the API and website.

1. Clone the team integration branch (or update an existing clone):

   ```powershell
   git clone https://github.com/ztdayyyyyyyyyy2112/GhostCustomer.git
   Set-Location GhostCustomer
   git switch develop
   git pull --ff-only origin develop
   ```

2. Download the [Retailrocket e-commerce dataset](https://www.kaggle.com/datasets/retailrocket/ecommerce-dataset), version 2. Put **only** its `events.csv` at `data/raw/events.csv`. Check that `Get-FileHash data/raw/events.csv -Algorithm SHA256` returns `3745aa83238b1e6d44d8fda209807899f420084398f94ddf745f3cbcfecbf9e7`. The pipeline also verifies the 94,237,913-byte source against `data/config/pipeline.json`. Do not commit the CSV.

3. Create the Python environment and rebuild the data, analyses and model. Calling the virtual environment's Python directly avoids PowerShell activation-policy issues:

   ```powershell
   py -3.12 -m venv .venv
   .\.venv\Scripts\python.exe -m pip install -r requirements-defense.txt
   .\.venv\Scripts\python.exe -m scripts.prepare_real_demo
   ```

   If `py -3.12` is unavailable, use an installed Python 3.12+ executable to create `.venv`. The final command takes several minutes. It generates local processed files and the ignored model binary, updates aggregate research outputs, and checks all seven API routes. On the **same machine**, when the processed files already exist and match the pinned source, `python -m scripts.prepare_real_demo --from-processed` can rerun the analyses; use `.\.venv\Scripts\python.exe` in place of `python`. Review any changed tracked result files before committing them.

4. Confirm the research artifacts before opening the website:

   ```powershell
   .\.venv\Scripts\python.exe scripts/check_integration_artifacts.py --require-complete
   .\.venv\Scripts\python.exe -m scripts.verify_real_demo
   ```

   The second command should report `"data_mode": "real"`, `"api_endpoints_checked": 7` and a model version. It also checks valid prediction and 404/422 error behavior. It runs without a separately started API server.

5. Configure the frontend in **real** mode. Copy the example, then edit `frontend/.env.local` to contain these values:

   ```powershell
   Copy-Item frontend/.env.example frontend/.env.local
   npm --prefix frontend ci
   ```

   ```dotenv
   NEXT_PUBLIC_API_MODE=real
   NEXT_PUBLIC_API_URL=http://localhost:8000
   NEXT_PUBLIC_MOCK_ERROR=0
   ```

   Keep `ENABLE_DEMO_FIXTURES` unset. `mock` and fixture modes are for interface testing and must not be presented as research results.

6. Start the API in **terminal A**, from the repository root:

   ```powershell
   .\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --port 8000
   ```

   Check <http://localhost:8000/health> and <http://localhost:8000/docs>.

7. Start the website in **terminal B**, from the same root:

   ```powershell
   npm --prefix frontend run dev
   ```

   Open <http://localhost:3000/dashboard>. Visit Customers, Statistics, Forecast, Prediction and Model Metrics. Stop the servers with `Ctrl+C`. Restart the frontend after changing `.env.local`; rebuild it after changing `NEXT_PUBLIC_*` values for a production run.

For a final local check, run `.\.venv\Scripts\python.exe -m pytest data/scripts/tests ai/tests research/baselines/tests research/forecasting/tests research/regression/tests backend/tests -q`, `npm --prefix frontend run lint`, and `npm --prefix frontend run build`. If the website displays sample values, check `NEXT_PUBLIC_API_MODE=real` and restart Next.js. If prediction returns 503, the local trained model is missing; repeat step 3. Do not replace the pinned CSV with another dataset version to bypass a hash mismatch.

The [research runbook](docs/runbook.md) explains the cohort and evaluation limits. The [eight-minute video script](docs/demo_video_8min.md) covers the website and every implemented algorithm. The [English full report](reports/full-report/GhostCustomer_STAT3013_Full_Report_EN.docx) contains the detailed methods and tables.

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
