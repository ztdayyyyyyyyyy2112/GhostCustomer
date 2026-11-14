# Evidence register

Use one row per reproducible output. The owner adds a relative path or stable URL, generating command/notebook, input version/hash, date, split/window, and reviewer before the output is copied into the report, paper, slides, API, or video. A dashboard screenshot alone is not the source of a study result.

| ID | Evidence and intended use | Owner | Source path / command / input version | Review status |
| --- | --- | --- | --- | --- |
| E-00 | Exploratory Retailrocket source and window feasibility audit; not a Ghost-label result | Thành; Lâm reviews | `research/feasibility/retailrocket_audit.md` and matching script; `events.csv` SHA-256 in report | Preliminary — not approved for final claims |
| E-01 | Dataset provenance, license, schema, raw hashes, coverage | Lâm | `docs/data_sources.md`, `data/README.md`, `data/config/pipeline.json`; source SHA-256 and verification command recorded | Preliminary — source/hash verified; D-01 approval pending |
| E-02 | Cohort flow and window/label sensitivity for D-02/D-03 | Lâm | Pending processed data | Pending |
| E-03 | Descriptive group tables and figures for RQ1 | Lâm / Long | Pending statistical pipeline | Pending |
| E-04 | Hypothesis tests, CIs, effect sizes, assumptions for RQ1 | Long | Pending statistical pipeline | Pending |
| E-05 | Linear/logistic regression coefficients and diagnostics for RQ2 | Long | Pending regression analysis | Pending |
| E-06 | Forecast series, naive baseline, holdout errors and intervals for RQ4 | Long | Pending forecasting analysis | Pending |
| E-07 | Temporal split, leakage audit, model comparison and calibration for RQ3 | Kiệt | Pending model pipeline | Pending |
| E-08 | Inference artifact/version and accepted API response examples | Kiệt / Long | Pending integration | Pending |
| E-09 | Lecturer guidance and SEM feasibility decision for D-07 | Thành / Long | Pending clarification | Pending |
| E-10 | Real-backend integration checks and demo evidence | Thành | `docs/integration_test.md`; backend foundation and fixture/empty-state HTTP smoke verified, real artifacts pending | Pending real-data check |
| E-11 | Decision Tree benchmark for RQ3 on the common temporal/visitor split | Thành | `research/baselines/decision_tree.py`; approved cohort, label and split inputs pending | Pending real-data evaluation and Kiệt review |

Before final submission, check that each table, figure, and numerical statement in all artifacts points to an approved evidence ID. Record any correction in a PR and update all affected artifacts together.
