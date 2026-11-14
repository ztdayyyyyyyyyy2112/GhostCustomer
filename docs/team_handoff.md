# Asynchronous team handoff

Updated 14 November 2026. This is a checklist for review across different working hours. The backend foundation and frontend can run together with empty states or clearly labeled fixtures. It is not a claim that the data, analysis, or inference model is finished. Reply in a PR or the decision log with the exact artifact path and any change needed in the shared API contract. See `docs/integration_handoff.md` for the file/function interface and acceptance checks.

## Thành — frontend and coordination

- Frontend routes now cover overview, customers, statistics, forecast, prediction, and model metrics. Mock mode is labeled as illustrative. Lint and production build pass locally.
- Own the Decision Tree benchmark for RQ3 in `research/baselines/`. Use Lâm's approved pre-T features and Kiệt's visitor-aware temporal split. Report its held-out metrics and limitations; it is not automatically the model served by `/api/predict`.
- Review UI copy against the eventual label definition, approve D-01–D-07 only with evidence, and compare real API responses using `docs/integration_test.md`.
- Keep the report, paper, slides, and video aligned with the evidence register. Resolve the repository naming convention before final submission.

## Lâm — dataset and cohort

- Delivered locally as preliminary E-01: provenance/license, verified raw hash, field dictionary, timestamp handling, event counts, visitor coverage, missingness, and duplicate summary. See `docs/data_sources.md` and `data/README.md`.
- Delivered locally as preliminary E-02: three B+O+C windows, 15/30/60-minute session gaps, theta sensitivity, no-purchase session-label variant, class counts, and censoring. Outputs are ignored under `data/processed/`; see `docs/data_go_no_go.md`. Recommend D-02–D-04 only after reviewing these outputs; Thành approval remains open.
- Supply processed-data schema and pre-T feature definitions. Review `Customer`, `CustomerWeekly`, repeated visitor snapshots, and the artifact format in `docs/integration_handoff.md`; flag any field the dataset cannot support.

## Long — statistical analysis, forecast, and backend

- Deliver reproducible descriptive tables, tests with assumptions/CIs/effect sizes, regression diagnostics, and weekly forecast evaluation (E-03–E-06). Use only fully observable future labels in rate denominators.
- Review the seven implemented FastAPI routes against actual analysis artifacts and propose schema changes in a PR. Keep empty results or explicit errors while artifacts are unavailable.
- Give the frontend one known-good real response and one error response per route. Review `docs/sem_feasibility_questions.md` with Thành and record lecturer guidance under D-07.

## Kiệt — modeling and inference

- Deliver the time/visitor split plan, leakage audit, majority/rule baselines, model comparison, calibration, threshold choice, and model card/artifact version (E-07).
- Agree on pre-T inference inputs and `POST /api/predict` response with Long. Provide `ai/inference/runtime.py` as described in `docs/integration_handoff.md`; a model binary alone cannot activate prediction. Supply feature attribution only if actually computed from the saved model; include the explanation method and limitations (E-08).
- Review the model metrics schema, especially `evaluation_context`, confusion-matrix orientation, support, prevalence, and calibration bins.

## Shared review gate

Before merging a contract change, the data, backend, AI, and frontend owners should agree on one example response, null/unknown behavior, dates/timezone, and error codes. Before recording a final demo or making a performance claim, link the exact evidence ID from `docs/evidence_register.md` and finish the real-backend integration matrix. The current UI and report draft are ready for this review, not for empirical claims.
