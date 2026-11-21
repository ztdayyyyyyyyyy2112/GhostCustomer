# Full report writing outline

Target: approximately 30 pages, excluding any course-specific front matter. This is a drafting guide, not a report containing results. A pre-data draft of Sections 1–3 is in `draft_sections_1_3.md`. Insert only values produced by the reproducible analysis and cite the exact notebook/table/figure source in `docs/evidence_register.md`. Keep the same label definition, dates, cohort counts, and model version across this report, the IEEE paper, slides, and dashboard.

## 1 Introduction

Explain the business problem of declining engagement, why it is useful to identify a warning stage before inactivity, and why an operational label is necessary. State the four questions from `docs/research_scope.md`, the unit of analysis, the intended contribution, and the limits of observational event data.

## 2 Related work

Review research on customer disengagement/churn, longitudinal behavioral features, temporal validation, statistical inference, calibration, and forecasting. Compare definitions and observation horizons; do not claim the proposed label is a recognized ground-truth state. Keep a source table with DOI/URL, data context, methods, limitations, and relevance. Verify every citation before writing the final text.

## 3 Dataset and methodology

Record source and usage terms, raw tables, event dictionary, timestamps/timezone, visitor coverage, missingness, duplicate handling, and cleaning log. Show how visitor-week observations and sessions are constructed. Define baseline, observation, snapshot T, confirmation horizon, eligible cohort, right-censoring, and unknown labels. Report a flow diagram with actual counts for each exclusion. Explain window/threshold sensitivity and the chosen setting from `docs/decision_log.md`.

Describe pre-T features and safeguards against target leakage. State train/validation/test dates, repeated-visitor handling, train-only preprocessing, software versions, random seeds, and the exact outcome definition. Distinguish a descriptive comparison of future-labeled groups from a deployable prediction made at T.

## 4 Descriptive and inferential statistics

For each comparison, show group sizes, missing values, distribution plot, central tendency, spread, and units. Present confidence intervals with the method used. For each test, give H0/H1, assumptions, sample independence or clustered treatment, statistic, p-value, effect size, CI when appropriate, and interpretation. Explain any multiple-testing correction.

## 5 Regression and statistical modeling

For linear regression, define a continuous dependent variable, predictors, formula, coefficients with CIs/p-values, fit measures, residual diagnostics, and limitations. For logistic regression, report odds ratios with CIs, multicollinearity checks, class balance, threshold choice, calibration, and held-out performance. Interpret associations without claiming causality.

## 6 SEM status

The course outline lists SEM. Record the lecturer's clarification and the feasibility decision in `docs/decision_log.md`. If valid latent constructs and measurement data exist, document the model and fit checks. Otherwise explain the limitation; do not create a survey or fit indices that were not observed.

## 7 Time-series forecasting

Define the weekly numerator and denominator using only fully observable labels. Show series length, train/test split, observed trend, naive baseline, and any ARIMA model supported by the data. Include method selection, residual checks, forecast horizon, intervals, and MAE/RMSE/sMAPE. If the series is too short, report that transparently.

## 8 Machine learning and inference

Compare majority/rule baselines with logistic, RF, and optional boosting using the same temporal split. Present test support, prevalence, confusion matrix, precision, recall, F1, ROC-AUC, PR-AUC, Brier/calibration, and threshold trade-offs. Describe model artifact/version, inference input schema, and feature attribution limits. Keep SHAP explanations separate from causal claims.

## 9 Results and discussion

Answer RQ1–RQ4 in order, using specific tables/figures and confidence statements. Compare statistical and ML findings; address sampling bias, operational proxy labels, censoring, unequal histories, leakage risks, short horizon, and practical limits of retention recommendations.

## 10 Conclusion and recommendations

State only supported findings, the conditions under which the demo could be useful, and future work. Avoid promises of business impact without intervention data.

## References and appendix

Use a consistent IEEE or APA reference style as required by the course. Include reproducibility commands, code/video links, data access steps, sensitivity tables, extra diagnostics, ethical considerations, and evidence of similarity/AI audit as required for submission. Final submission checks live in `docs/submission_checklist.md`.
