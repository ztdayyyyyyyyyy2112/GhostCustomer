# Asynchronous team handoff

Updated 8 November 2026. This is a checklist for review across different working hours. It is not a claim that the data, analysis, or backend is finished. Reply in a PR or the decision log with the exact artifact path and any change needed in the shared API contract.

## Thành — frontend and coordination

- Frontend routes now cover overview, customers, statistics, forecast, prediction, and model metrics. Mock mode is labeled as illustrative. Lint and production build pass locally.
- Review UI copy against the eventual label definition, approve D-01–D-07 only with evidence, and compare real API responses using `docs/integration_test.md`.
- Keep the report, paper, slides, and video aligned with the evidence register. Resolve the repository naming convention before final submission.

## Lâm — dataset and cohort

- Deliver a provenance/license record, raw hashes, field dictionary, timestamp handling, event counts, visitor coverage, missingness, and duplicate summary (E-01).
- For candidate time windows, provide eligible snapshot counts, ghost/active/unknown counts, censoring, and sensitivity of label and session rules (E-02). Propose D-02–D-04 decisions from those results.
- Supply processed-data schema and pre-T feature definitions. Review `Customer`, `CustomerWeekly`, and `GET /api/customers*` fields in `docs/api_contract.md`; flag any field the dataset cannot support.

## Long — statistical analysis, forecast, and backend

- Deliver reproducible descriptive tables, tests with assumptions/CIs/effect sizes, regression diagnostics, and weekly forecast evaluation (E-03–E-06). Use only fully observable future labels in rate denominators.
- Implement and document the seven routes in `docs/api_contract.md`, or propose schema changes in a PR. Return empty results or explicit errors while analysis artifacts are unavailable.
- Give the frontend one known-good real response and one error response per route. Review `docs/sem_feasibility_questions.md` with Thành and record lecturer guidance under D-07.

## Kiệt — modeling and inference

- Deliver the time/visitor split plan, leakage audit, majority/rule baselines, model comparison, calibration, threshold choice, and model card/artifact version (E-07).
- Agree on pre-T inference inputs and `POST /api/predict` response with Long. Supply feature attribution only if actually computed from the saved model; include the explanation method and limitations (E-08).
- Review the model metrics schema, especially `evaluation_context`, confusion-matrix orientation, support, prevalence, and calibration bins.

## Shared review gate

Before merging a contract change, the data, backend, AI, and frontend owners should agree on one example response, null/unknown behavior, dates/timezone, and error codes. Before recording a final demo or making a performance claim, link the exact evidence ID from `docs/evidence_register.md` and finish the real-backend integration matrix. The current UI and report draft are ready for this review, not for empirical claims.
