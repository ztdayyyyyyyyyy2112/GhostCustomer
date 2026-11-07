# Full report draft: Introduction, related work, and methods

**Status:** pre-data draft, 8 November 2026. This text contains no study finding. Replace bracketed decision fields only after the dataset audit and decision log are approved. Cross-check all final statements with `docs/evidence_register.md` and use the citation style required by the course.

## 1. Introduction

An e-commerce visitor can reduce engagement without disappearing immediately. This intermediate pattern may matter for retention planning, but event logs do not reveal a person's intent or prove that they have left. We therefore use *ghost customer* as a proposed operational label for a future behavior pattern, defined by observable events and a fixed confirmation horizon. The label must be finalized from dataset coverage and sensitivity checks before it is used in statistical tests or model training.

The project's prediction point is a dated snapshot, **T**. Features available up to T describe earlier visitor activity; events after T are reserved for constructing and checking the outcome. This separation allows a retrospective analysis of future-labeled groups and a prospective prediction task to share one time boundary. A visitor can contribute more than one snapshot, so observations may be dependent and need explicit treatment in validation and inference.

The study asks four questions: (1) how pre-T behavior differs between visitors later labeled ghost and active; (2) which pre-T signals are associated with the outcome; (3) whether a predictive model improves on simple baselines on later data; and (4) whether the weekly ghost rate can be forecast at a useful horizon. These questions are specified in `docs/research_scope.md`. The intended contribution is a reproducible event-data definition and evaluation workflow, connected to a web interface that displays provenance, uncertainty, and unavailable results honestly. Claims about customer psychology, causality, or retention campaign impact are outside the evidence available from observational event logs alone.

## 2. Related work

Customer churn studies show the value of explicit predictive evaluation, while also illustrating that outcome definitions depend on the business setting. Neslin et al. compared churn-model submissions on validation databases in a telecommunications context [R1]. Their outcome is not interchangeable with this project's proposed e-commerce engagement label; the relevant methodological lesson is to compare methods on a common held-out evaluation. Burez and Van den Poel examined class imbalance in churn prediction [R2]. Their work motivates recording the ghost and non-ghost counts before choosing a metric or resampling strategy, but it does not establish what the prevalence will be here.

If the positive class is uncommon, a single discrimination score can conceal how many flagged visitors are actually positive. Saito and Rehmsmeier analyze interpretation of precision-recall and ROC plots under class imbalance [R3]. We plan to report PR-AUC with class prevalence, precision, recall, threshold, and support, alongside ROC-AUC. Probability quality is a separate question from ranking. Guo et al. study calibration of modern neural networks [R4]; their results justify checking calibration of the eventual risk scores but do not imply that any model in this project is already calibrated.

Per-prediction attribution can help a reviewer inspect a fitted model's output. Lundberg and Lee introduce SHAP as a framework for assigning feature contributions to a prediction [R5]. Such values describe model behavior under an explanation method; they do not show that changing a customer's feature would change future behavior. The dashboard will show factors only when supplied by the trained inference pipeline. No fabricated attribution is used in the demonstration.

The literature does not supply a validated ghost label for the chosen dataset. The study must document its own eligible cohort, time windows, threshold sensitivity, right-censoring, and validation design. Dataset-specific and temporal-validation references will be added after D-01, D-02, and D-05 are resolved.

## 3. Data and methodology

### 3.1 Source and audit

The candidate source is Retailrocket event data, subject to a source/license and coverage audit [D-01]. The final report will give the exact dataset version, acquisition date, permitted use, raw file hashes, schema, event types, timestamp timezone, unique visitor count, observation period, missingness, duplicates, and processing exclusions. These are currently **unavailable**. A longer event dataset is a fallback if the candidate does not yield enough fully observed visitor histories. The audited data dictionary and cohort flow will be linked in `docs/evidence_register.md`.

### 3.2 Time design and operational outcome

The unit of analysis is a visitor at snapshot T. A baseline interval and an observation interval end at or before T; a confirmation interval begins after T. The final lengths are `[D-02: baseline]`, `[D-02: observation]`, and `[D-02: confirmation]`. Sessions, views, carts, purchases, active days, recency, and decay are candidate pre-T features. Their final formulas and missing-value rules will be recorded before evaluation. A proposed 30-minute session gap is an audit assumption, not a settled parameter [D-04].

The future ghost, active, recovered, and inactive states require `[D-03: label rule and threshold]`. A row whose complete confirmation horizon is not observable receives `unknown`; it is not treated as a negative supervised example. The report will show a flow from raw visitors to eligible snapshots and final labels, including counts removed by each rule. Window and threshold sensitivity will be compared before the label is fixed. Future events may be shown in the dashboard's retrospective confirmation timeline, but they must never enter predictors or be sent to inference as pre-T features.

### 3.3 Descriptive statistics and inference

For each outcome group, report N, missing values, units, distribution, central tendency, spread, and confidence intervals. Pre-specify comparisons for RQ1, check assumptions, and select a parametric or rank-based test appropriate to the distribution. If repeated snapshots are analyzed, either select an independent visitor-level sample or use a method that accounts for visitor clustering. Each result will include H0/H1, statistic, p-value, effect size, confidence interval where applicable, and a statement about uncertainty. Linear regression, if used, needs a clearly continuous outcome and residual checks; logistic regression uses the future binary outcome and reports odds ratios, intervals, class balance, and diagnostics. Associations will not be described as causal effects.

### 3.4 Prediction and forecasting

Prediction candidates are majority and simple engagement-rule baselines, logistic regression, random forest, and optional boosting. Split dates and repeated-visitor handling remain `[D-05: temporal validation plan]`. Fit imputation, scaling, feature selection, and any resampling using training data only. Choose hyperparameters and operating threshold on validation data, then evaluate once on a held-out later set. Report support, prevalence, confusion matrix, precision, recall, F1, ROC-AUC, PR-AUC, Brier score, and calibration. Preserve model version and input schema with the saved artifact.

The forecast target is the weekly ghost rate among eligible snapshots whose future outcome is fully observable. Its numerator, denominator, date alignment, series length, and holdout dates will be explicit. Compare a last-observation baseline with ARIMA only if the usable series and diagnostics support the latter [D-06]. Display observed, fitted, and future periods separately, with intervals and MAE/RMSE/sMAPE where calculable. If the series is too short, report the limitation instead of extrapolating an unsupported forecast.

### 3.5 SEM and reproducibility

The course outline lists SEM, but the current event-log design has no specified latent measurement model. The team will seek lecturer clarification using `docs/sem_feasibility_questions.md` and record the decision under D-07. No SEM coefficient or fit index will appear unless identification and measurement validity can be justified.

The final methods section will list software versions, seeds, exact scripts, file hashes, and commands that regenerate every table and figure. The frontend reads published outputs through `docs/api_contract.md`; it must not serve as the sole source for a reported number.

## References to format for the final report

- [R1] S. A. Neslin et al., “Defection Detection: Measuring and Understanding the Predictive Accuracy of Customer Churn Models,” *Journal of Marketing Research*, vol. 43, no. 2, 2006. https://doi.org/10.1509/jmkr.43.2.204
- [R2] J. Burez and D. Van den Poel, “Handling class imbalance in customer churn prediction,” *Expert Systems with Applications*, vol. 36, no. 3, pp. 4626–4636, 2009. https://doi.org/10.1016/j.eswa.2008.05.027
- [R3] T. Saito and M. Rehmsmeier, “The Precision-Recall Plot Is More Informative than the ROC Plot When Evaluating Binary Classifiers on Imbalanced Datasets,” *PLOS ONE*, vol. 10, no. 3, e0118432, 2015. https://doi.org/10.1371/journal.pone.0118432
- [R4] C. Guo, G. Pleiss, Y. Sun, and K. Q. Weinberger, “On Calibration of Modern Neural Networks,” *Proceedings of Machine Learning Research*, vol. 70, pp. 1321–1330, 2017. https://proceedings.mlr.press/v70/guo17a.html
- [R5] S. M. Lundberg and S.-I. Lee, “A Unified Approach to Interpreting Model Predictions,” *Advances in Neural Information Processing Systems*, vol. 30, 2017. https://proceedings.neurips.cc/paper_files/paper/2017/hash/8a20a8621978632d76c43dfd28b67767-Abstract.html
