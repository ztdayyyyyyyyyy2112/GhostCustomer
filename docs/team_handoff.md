# Asynchronous team handoff

Updated 15 November 2026. This is a checklist for review across different working hours. The backend foundation and frontend can run together with empty states or clearly labeled fixtures. It is not a claim that the data, analysis, or inference model is finished. Reply in a PR or the decision log with the exact artifact path and any change needed in the shared API contract. See `docs/integration_handoff.md` for the file/function interface and acceptance checks.

## Thành — frontend and coordination

- Frontend routes now cover overview, customers, statistics, forecast, prediction, and model metrics. Mock mode is labeled as illustrative. Lint and production build pass locally.
- Own the Decision Tree benchmark for RQ3 in `research/baselines/`. Use the proposed pre-T features after the cohort/label decisions and Kiệt's visitor-aware temporal split, and evaluate on the same split as the Gaussian Naive Bayes baseline. Report held-out metrics and limitations; it is not automatically the model served by `/api/predict`.
- Review UI copy against the eventual label definition, approve D-01–D-07 only with evidence, and compare real API responses using `docs/integration_test.md`.
- Keep the report, paper, slides, and video aligned with the evidence register. Resolve the repository naming convention before final submission.

## Lâm — dataset and cohort

- Delivered locally as preliminary E-01: provenance/license, verified raw hash, field dictionary, timestamp handling, event counts, visitor coverage, missingness, and duplicate summary. See `docs/data_sources.md` and `data/README.md`.
- Delivered locally as preliminary E-02: three B+O+C windows, 15/30/60-minute session gaps, theta sensitivity, no-purchase session-label variant, class counts, and censoring. Outputs are ignored under `data/processed/`; see `docs/data_go_no_go.md`. Recommend D-02–D-04 only after reviewing these outputs; Thành approval remains open.
- Supply processed-data schema and pre-T feature definitions. Review `Customer`, `CustomerWeekly`, repeated visitor snapshots, and the artifact format in `docs/integration_handoff.md`; flag any field the dataset cannot support.
- Own the Gaussian Naive Bayes baseline for RQ3, assigned by the team lead on 15 November. Runner: `research/baselines/gaussian_nb.py`; method and run contract: `research/baselines/GAUSSIAN_NAIVE_BAYES.md`. Describe its conditional-independence assumption and limitations; use the approved pre-T features and the same visitor-aware temporal split, validation protocol, and untouched test set as Thành's Decision Tree. Coordinate with Kiệt; real-data evaluation waits for the shared split, feature allowlist, and label decisions.

## Long — statistical analysis, forecast, and backend

- Own E-03 descriptive tables, including sample SD and per-group feature missing counts/rates, then deliver hypothesis tests with assumptions/CIs/effect sizes, regression diagnostics, and weekly forecast evaluation (E-04–E-06). Use only mature, fully labeled rows for E-03 and fully observable future labels in rate denominators. Lâm reviews E-03 data/cohort inputs.
- Review the seven implemented FastAPI routes against actual analysis artifacts and propose schema changes in a PR. Keep empty results or explicit errors while artifacts are unavailable.
- Give the frontend one known-good real response and one error response per route. Review `docs/sem_feasibility_questions.md` with Thành and record lecturer guidance under D-07.

## Kiệt — modeling and inference

- Implemented in `ai/` (see `ai/README.md`): visitor-aware temporal split with strict purging and manifest (D-05 proposal), leakage audit, majority/EDS baselines, logistic regression, random forest, gradient boosting, optional SVM/Isolation Forest, train-only preprocessing, Platt calibration, visitor-bootstrap CIs, validation-chosen cost threshold and risk bands, circularity ablation, permutation/SHAP/attribution explanations, model card, and `ai/inference/runtime.py`.
- First real-data run (17 Nov, window 4+2+2) is committed in `ai/evaluation/`. The write-up is `reports/full-report/ml_results.md` and the notebooks are in `ai/notebooks/`. Selected XGBoost+Platt: test PR-AUC 0.928 [0.887, 0.958]. The score is driven mostly by baseline level (regression to the mean); see the circularity notes. A 4+2+4 rerun follows the lecturer's feedback.
- The real run writes `data/processed/modeling_snapshots.csv` (SHA-256 `f39af409…`), the shared split for Thành's Decision Tree and Lâm's Gaussian NB. Kiệt ran both scripts on it: DT test PR-AUC 0.927, GNB 0.667 (`ai/evaluation/benchmark_shared_split.json`); owners please confirm.
- Long: the model file is shared privately (SHA-256 in `ai/evaluation/model_meta.json`). Run `python -m ai.inference.examples` to produce `docs/predict_examples.json`, then compare it with the live `/api/predict` responses.
- Long: `runtime.predict` raises `LookupError`/`ValueError`/`RuntimeError` (404/422/503). `model_service` now treats `RuntimeError` (runtime present, artifacts missing) as "no model", so demo fixtures keep working; tests isolate `MODELS_DIR`.

## Shared review gate

Before merging a contract change, the data, backend, AI, and frontend owners should agree on one example response, null/unknown behavior, dates/timezone, and error codes. Before recording a final demo or making a performance claim, link the exact evidence ID from `docs/evidence_register.md` and finish the real-backend integration matrix. The current UI and report draft are ready for this review, not for empirical claims.
