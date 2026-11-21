# Local real-data runbook for Ghost Customer Prediction

## What this build demonstrates

The 20 November 2026 rebuild from the pinned Retailrocket `events.csv` produced 97,489 visitor snapshots, 97,489 local detail files, exploratory statistics, regression outputs, a 12-week rate series with a naive forecast, and a trained model. The seven FastAPI routes passed `python -m scripts.verify_real_demo` with real artifacts. This is a course research prototype under the **proposed** 4+2+2 cohort and operational Ghost label. It is not validated churn detection. The raw dataset, customer-level processed files, and binary model are ignored by Git and must be regenerated on the demo machine.

## Prepare one demo machine

1. Clone the repository and use Python 3.12 or newer and Node.js 24. Download Retailrocket Kaggle dataset version 2 from <https://www.kaggle.com/datasets/retailrocket/ecommerce-dataset>. Place only `events.csv` at `data/raw/events.csv`. Do not commit it. The pipeline verifies the pinned 94,237,913-byte file and SHA-256 `3745aa83238b1e6d44d8fda209807899f420084398f94ddf745f3cbcfecbf9e7` before processing.
2. Create and activate a virtual environment, then run from the repository root:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   python -m pip install -r requirements-defense.txt
   python -m scripts.prepare_real_demo
   ```

   The orchestrator runs the data pipeline, sensitivity and detail export, inferential analysis, forecast, OLS and logistic regressions, AI training, Decision Tree and Gaussian NB on the shared split, structural checks, and real API smoke. It writes only aggregate research results to tracked files. Use `--from-processed` to rerun the analysis and model when the verified processed files already exist locally.
3. Start FastAPI from the repository root in a separate terminal:

   ```powershell
   .\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --port 8000
   ```

   Leave `ENABLE_DEMO_FIXTURES` unset. Check <http://localhost:8000/docs> and run `python -m scripts.verify_real_demo` after any artifact change.
4. Copy `frontend/.env.example` to `frontend/.env.local` and set `NEXT_PUBLIC_API_MODE=real` and `NEXT_PUBLIC_API_URL=http://localhost:8000`. From `frontend/`, run `npm ci`, `npm run lint`, `npm run build`, then `npm run dev`. Open <http://localhost:3000/dashboard>. Restart/rebuild the frontend after changing `NEXT_PUBLIC_*` values.

## Defense flow and facts to keep distinct

Go through Overview, Customers, one customer timeline, Statistics, Forecast, Prediction, and Model Metrics. Choose a Ghost row from the customer list for the prediction example and keep its dated snapshot. Show an unknown ID or invalid date as the error case. The interface also has a mock mode for UI development; it must be introduced as illustrative if used.

- The overview includes all 97,489 history-eligible snapshots, including repeated visitors and censored rows. Its `ghost_rate` uses all displayed snapshots as denominator. It is not the same population as the prediction task.
- The inferential test uses one latest mature snapshot per visitor and compares Ghost with Active. The OLS outcome is future sessions per week and includes all mature label statuses. The logistic analysis uses Ghost versus the other mature statuses. The AI classifier uses Ghost versus Active and a separate purged visitor/time split. Do not compare their prevalence or thresholds as if they shared a denominator.
- The weekly Ghost-rate forecast has only 12 mature points. Its last-value baseline was checked at three historical origins; ARIMA was not selected. Two future points are shown without intervals. The numerical forecast is exploratory and not evidence of stable long-horizon performance.
- The served full-feature XGBoost model has test PR-AUC 0.928 on 430 held-out Ghost/Active rows. The stricter observation-only ablation falls to 0.607. Baseline-history dependence is a central result, not a footnote. The 0.05 alert threshold assumes a false negative cost five times a false positive cost and causes the medium/high bands to coincide.
- SEM has no justified measurement model in the event log. The course outline lists it; obtain lecturer guidance before claiming completion or an approved omission. See `docs/sem_feasibility.md`.

Use `research/statistics/results.json`, `research/regression/results/`, `research/forecasting/analysis_manifest.json`, `ai/evaluation/`, and `docs/evidence_register.md` to answer numerical questions. The dashboard is a display of those artifacts, not their source. `docs/demo_video_8min.md` gives the timed recording script covering every implemented algorithm.

## Verification and recovery

Run `python -m pytest data/scripts/tests ai/tests research/baselines/tests research/forecasting/tests research/regression/tests backend/tests -q`, `python scripts/check_integration_artifacts.py --require-complete`, and `python -m scripts.verify_real_demo`. From `frontend/`, run `npm run lint` and `npm run build`. If the model is missing, regenerate it with `python -m ai.training.run --optional-models` and `python -m ai.evaluation.report` after installing `requirements-defense.txt`; check its SHA-256 against `ai/evaluation/model_meta.json`. If processed files change, rerun `python -m scripts.prepare_real_demo --from-processed` so the hashes, results and model agree.

The English full report is at `reports/full-report/GhostCustomer_STAT3013_Full_Report_EN.docx` (29 A4 pages; editable source `GhostCustomer_Full_Report_EN.md`). The provisional IEEE paper remains at `reports/ieee-paper/paper_draft.docx` (7 pages, two columns), and the presentation draft is `reports/slides/defense_deck.pptx` (12 slides). The report still needs the team's final factual/signature review and the lecturer's SEM decision; the paper still needs the official IEEE template and pagination check.

The submission still requires a final reviewed full report, a 7–10-page IEEE-template paper, a narrated demo video, academic integrity screenshots, lecturer decision on SEM, and the course system uploads. Confirm the final repo name against `STAT3013.QXX_GroupYY` using the class and group codes before renaming it.
