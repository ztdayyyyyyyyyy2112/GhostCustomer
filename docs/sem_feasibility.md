# BE-13 SEM feasibility assessment

Owner: Dang Hoang Long (24520995). Prepared 9 November 2026. Status: preliminary assessment for D-07 / E-09; lecturer clarification pending. This is a feasibility deliverable, not a fitted SEM, course exemption or approval of a substitute method.

## Evidence reviewed

- The supplied task allocation assigns BE-13 to assess the SEM requirement. The original course outline/rubric and the lecturer's answer have not been provided for this implementation.
- `docs/sem_feasibility_questions.md` already lists the questions to ask; no answer is recorded in D-07.
- The exploratory Retailrocket audit describes visitor event logs, repeated snapshots and only a short set of eligible weekly dates. It does not identify a validated latent measurement model.
- The current API and report outlines appropriately leave empirical evidence pending. No SEM estimates, fit indices, survey responses or latent scores are supplied.

## Assessment

Event data do not categorically rule out SEM, and a survey is not universally required. However, click/session counts cannot simply be renamed as validated indicators of a psychological construct. A defensible analysis first needs a theoretical construct definition, a specified measurement/structural model and a sampling design that handles repeated visitors and temporal ordering.

The current study can describe pre-T behavioral features and test associations with a future operational outcome. That supports the proposed regression/logistic workflow subject to its assumptions. It does not establish latent construct validity, causal mediation or the lecturer's acceptance of observed-variable path analysis as SEM.

## Decision options

| Option | Required evidence before implementation | Current status |
|---|---|---|
| Latent-variable SEM using behavioral indicators | Theory, indicator rationale, identified measurement model, suitable sample, missingness plan, dependence treatment, reliability/validity and fit checks | Not specified |
| SEM using genuinely collected survey indicators | Valid instrument, ethical collection and adequate sample linked to the research question; measurement and structural model | No survey supplied; do not synthesize responses |
| Observed-variable path model | Lecturer accepts this interpretation; theoretical paths, temporal order, adequate identification and explicit noncausal interpretation | Await lecturer decision |
| Document SEM infeasibility and retain supported regressions | Lecturer approves omission or rubric permits a justified limitation | Not yet approved |

No option is silently selected. There is no universal sample-size number that makes an unspecified SEM valid. Assess adequacy for the actual estimator, number of parameters, dependence and indicator distributions.

## Lecturer clarification to record

Use the existing questions in `docs/sem_feasibility_questions.md`. Record the original rubric wording, lecturer response, date, participants, allowed alternative and exact reporting conditions in D-07. Link that evidence under E-09. No message or invitation has been sent as part of this task.

If SEM is required, pre-specify the candidate model and assess identification and indicator quality before fitting. Report the estimator, missing-data treatment, loadings/paths with uncertainty, fit diagnostics and limitations; do not report causal effects from observational paths without a justified identification design. If omitted, quote the approved limitation in the final report and keep its scope precise.

## Report wording until clarification

“Structural equation modeling has not been implemented because the current event-log study has no specified and validated measurement model. The team is seeking clarification of the course requirement and acceptable alternatives. The present analysis is limited to the descriptive, inferential, regression and forecasting methods supported by the observed data.”

## Acceptance checklist

- [x] Existing event-data evidence and missing measurement assumptions identified.
- [x] Viable decision paths and their prerequisites documented.
- [x] No fabricated SEM outputs or invented permission.
- [ ] Original course outline and lecturer decision recorded.
- [ ] D-07 approved and E-09 populated, or valid SEM completed if required.

The first three items complete the independently actionable assessment. The remaining items require actual course guidance and, if applicable, additional validated data.
