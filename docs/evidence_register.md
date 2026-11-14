# Evidence register

Use one row per reproducible output. The owner adds a relative path or stable URL, generating command/notebook, input version/hash, date, split/window, and reviewer before the output is copied into the report, paper, slides, API, or video. A dashboard screenshot alone is not the source of a study result.

| ID | Evidence and intended use | Owner | Source path / command / input version | Review status |
| --- | --- | --- | --- | --- |
| E-00 | Exploratory Retailrocket source and window feasibility audit; not a Ghost-label result | Thành; Lâm reviews | `research/feasibility/retailrocket_audit.md` and matching script; `events.csv` SHA-256 in report | Preliminary — not approved for final claims |
| E-01 | Dataset provenance, license, schema, raw hashes, coverage | Lâm | `docs/data_sources.md`, `data/README.md`, `data/config/pipeline.json`; source SHA-256 and verification command recorded | Preliminary — source/hash verified; D-01 approval pending |
| E-02 | Cohort flow and window/label sensitivity for D-02/D-03 | Lâm | Reproduce with `node research/feasibility/retailrocket_sensitivity.mjs` (eligibility thresholds read from `data/config/pipeline.json`) and `python -m data.scripts.run_pipeline --mode audit_compat`; current local output hashes: `data/processed/manifest.json`; active-week comparison: `research/feasibility/retailrocket_sensitivity.md`; full local outputs remain ignored under `data/processed/` | Preliminary — three windows, 2/3 active-week eligibility, session gaps, theta, no-purchase, and duplicate-exclusion sensitivities computed; D-01–D-04 remain pending approval |
| E-03 | Descriptive group tables for RQ1, including sample SD and feature missingness by mature label group | Long; Lâm reviews | `research/statistics/results.json`, generated from `data/processed/descriptive_statistics.json` by `python -m data.scripts.run_pipeline --mode audit_compat`; local `data/processed/manifest.json` records output hashes | Preliminary — descriptive only; repeated snapshots, no inference; Long owns analysis and Lâm review pending |
| E-04 | Hypothesis tests, CIs, effect sizes, assumptions for RQ1 | Long | Pending statistical pipeline | Pending |
| E-05 | Linear/logistic regression coefficients and diagnostics for RQ2 | Long | Pending regression analysis | Pending |
| E-06 | Forecast series, naive baseline, holdout errors and intervals for RQ4 | Long | Pending forecasting analysis | Pending |
| E-07 | Temporal split, leakage audit, shared-split model comparison and calibration for RQ3, including Gaussian Naive Bayes | Kiệt (split/comparison); Lâm (Gaussian Naive Bayes baseline) | Baseline runner: `research/baselines/gaussian_nb.py`; method/run contract: `research/baselines/GAUSSIAN_NAIVE_BAYES.md`; split manifest and benchmark outputs pending | Runner implemented and synthetic-tested; real-data evaluation pending approved split, feature allowlist, and label decisions |
| E-08 | Inference artifact/version and accepted API response examples | Kiệt / Long | Pending integration | Pending |
| E-09 | Lecturer guidance and SEM feasibility decision for D-07 | Thành / Long | Pending clarification | Pending |
| E-10 | Real-backend integration checks and demo evidence | Thành | `docs/integration_test.md`; backend foundation and fixture/empty-state HTTP smoke verified, real artifacts pending | Pending real-data check |
| E-11 | Decision Tree benchmark for RQ3 on the common temporal/visitor split | Thành | `research/baselines/decision_tree.py`; approved cohort, label and split inputs pending | Pending real-data evaluation and Kiệt review |

Before final submission, check that each table, figure, and numerical statement in all artifacts points to an approved evidence ID. Record any correction in a PR and update all affected artifacts together.
