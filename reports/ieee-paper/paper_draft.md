# Operational Ghost Customer Prediction from Retailrocket Event Histories

**STAT3013 conference paper draft for team and lecturer review, 20 November 2026.** The 4+2+2 setting and SEM treatment are not yet approved. The paper must be placed in the official IEEE conference template and checked for 7–10 pages before submission.

## Abstract

An e-commerce visitor can reduce activity without providing a direct churn label. We define an operational Ghost outcome as low future session activity relative to a visitor's own earlier baseline and study it using the public Retailrocket event log. A verified 2,756,101-event file yields 97,489 history-eligible weekly snapshots under a proposed 4+2+2-week design. We compare pre-snapshot behavior, fit continuous and binary regressions, test a short weekly rate forecast, and evaluate machine-learning models on a visitor-disjoint temporal split. In a one-snapshot-per-visitor comparison, Ghost visitors have 11.39 more days of pre-snapshot recency than Active visitors on average (95% CI 10.27–12.51). A selected XGBoost model reaches test PR-AUC 0.928 on 430 Ghost/Active rows, but a stricter observation-only feature set reaches 0.607. The 12-week mature rate series supports only an exploratory naive forecast. The results demonstrate a reproducible research and web-demo pipeline, while highlighting construct validity, baseline dependence, and short temporal coverage.

**Index terms:** Customer engagement, event logs, operational labels, temporal validation, precision-recall, forecasting.

## I Introduction

Most online shops can observe event sequences but cannot directly observe whether a silent visitor intends to leave. A behavioral label can make the problem measurable, yet it must be distinguished from true churn or customer intent. We use weekly snapshots T, extract only behavior before T, and assign a later operational state after a fully observed confirmation interval. The study asks whether pre-T behavior differs by future label, whether regression explains future activity, whether models rank future Ghost snapshots above simple baselines, and whether the weekly Ghost rate can be forecast.

Prior churn work shows the importance of out-of-sample comparison [1], while class imbalance changes the interpretation of error rates [2], [3]. We therefore report support, prevalence, PR-AUC, ROC-AUC, precision, recall, calibration, and explicit thresholds. Our contribution is a reproducible integration of data provenance, statistical analysis, predictive modeling, and a web demo, with a direct sensitivity check for the relative label's use of baseline activity.

## II Related Work

Neslin et al. [1] compare customer churn predictions in a validation tournament. That work motivates a common test set, but their observed outcome differs from the event-log proxy used here. Burez and Van den Poel [2] investigate imbalance in churn data; our own positive prevalence ranges from about 2% to 25% depending on task and denominator, so a single unqualified score would mislead. Saito and Rehmsmeier [3] show the usefulness of precision-recall analysis under imbalance. We use average precision as PR-AUC and always pair it with test prevalence. Guo et al. [4] motivate probability calibration checks, while Lundberg and Lee [5] provide a framework for explaining a fitted model. Attribution does not identify causal reasons for disengagement.

## III Data and Outcome Definition

The source is Retailrocket's Kaggle dataset v2 [6]. The local `events.csv` has 2,756,101 rows, 94,237,913 bytes and SHA-256 `3745aa83238b1e6d44d8fda209807899f420084398f94ddf745f3cbcfecbf9e7`. Anonymous `visitorid` values are treated as event identifiers rather than verified people. Timestamps are converted from milliseconds to UTC; a proposed session uses a 30-minute inactivity gap. The final observation boundary is 14 September 2015.

The proposed design uses four baseline weeks B, two observation weeks O and two confirmation weeks C. A visitor must have at least five pre-T events, activity in at least two history weeks, and baseline activity. Features such as sessions, views, cart actions, purchases, recency and decay come only from times before T. The ratio of confirmation sessions per week to baseline sessions per week defines Ghost when it is below 0.5 and future events are present. Zero future events become Inactive; an observation decline followed by improvement becomes Recovered. An incomplete confirmation horizon becomes Unknown with a null target. These are operational definitions, not observed churn labels.

The configuration yields 97,489 history-eligible visitor snapshots across 14 Mondays and 27,327 distinct visitor IDs. Only 85,899 snapshots have mature labels; 11,590 are censored. The mature counts are 2,619 Ghost, 9,263 Active, 2,716 Recovered and 71,301 Inactive. Repeated visitor snapshots cannot be interpreted as independent people. The 4+3+2 and 6+2+4 sensitivities yield 100,140 and 128,323 history-eligible snapshots respectively, but the latter has 40,043 censored rows. Ghost counts also change with the threshold and session gap. D-01 through D-04 remain open decisions.

| State | Snapshots | Use in primary ML |
| --- | ---: | --- |
| Ghost | 2,619 | Positive, if mature |
| Active | 9,263 | Negative, if mature |
| Recovered | 2,716 | Excluded |
| Inactive | 71,301 | Excluded |
| Immature/unknown | 11,590 | Excluded |

This table reports the source cohort before temporal purging and visitor partitioning. The web dashboard includes every history-eligible snapshot; the primary classifier uses only Ghost/Active rows and a smaller visitor-disjoint test. Consequently the dashboard Ghost fraction, the logistic-test prevalence, and the ML-test prevalence are not interchangeable estimates.

## IV Statistical and Regression Methods

Descriptive tables retain all mature rows in each status and report observed N, missingness, mean, standard deviation, median, quartiles and histograms for seven pre-T measures. Inferential comparison uses each visitor's latest mature snapshot and then selects Ghost and Active visitors. A two-sided Welch test compares mean recency; a Welch 95% confidence interval and Cohen d quantify uncertainty and effect size. A Wilson interval describes the Ghost proportion in that selected population. This sampling choice avoids duplicate rows from one visitor in the primary test but can still create selection bias.

The continuous regression response is sessions in the two-week future interval divided by two. OLS predictors are pre-T four-week sessions, views and recency. A simple sessions-only model provides a comparison. Temporal train/test separation requires mature training outcomes before the cutoff and excludes test visitors seen in training. Clustered covariance handles repeated training visitors. Residual and influence diagnostics check the linear fit; negative predictions flag its poor compatibility with a count response.

A separate logistic model takes Ghost versus all other mature statuses, with four-week sessions, recency and observation-minus-baseline engagement change as predictors. Train, validation and test segments are separated in time. Labels that cross the next partition start are purged, and repeated visitors cannot cross partitions. Coefficient intervals and odds ratios describe associations. Validation chooses the classification threshold, and test data are not used for that choice.

## V Forecast and Classification Methods

The forecast target is the weekly Ghost count divided by all known mature labels in a Monday bin. Unknown labels never become negatives. Each historical prediction uses only label periods ending strictly before its origin. We compare a last-mature-value naive baseline with ARIMA candidates only when sufficient mature history and validation origins exist. The usable series has 12 weeks, below the 40-week ARIMA selection condition, so no ARIMA claim or interval is made.

The primary ML task differs from the logistic inference task: it compares mature Ghost with Active snapshots only. A visitor-aware temporal split with label purging yields 2,214 train rows, 454 validation rows and 430 test rows, with 433, 119 and 109 Ghost labels. Candidate methods include the no-skill prior, a simple engagement-decay score, logistic regression, random forest, XGBoost, Decision Tree and Gaussian Naive Bayes; optional SVM and Isolation Forest are rank-only comparisons. Model family and hyperparameters are selected on validation PR-AUC. Platt calibration is fit from training out-of-fold predictions and retained only if validation Brier improves. The operating threshold minimizes a stated validation cost with a false-negative cost of five and false-positive cost of one. A 500-resample visitor bootstrap provides test PR-AUC intervals.

To examine label circularity, we compare the 41-feature full set with two restricted alternatives. Removing named baseline, decay and engagement-decay features still leaves overlapping six- and two-week counts from which baseline activity can be reconstructed. A stricter ten-feature set keeps only one- and two-week observation counts and excludes all baseline-period counts. This check asks whether the apparent predictive strength depends on the baseline in the label definition.

## VI Results

The descriptive Ghost snapshot group has mean four-week sessions 9.19 and mean recency 10.94 days; the Active group has 8.08 sessions and 4.90 days. These are repeated-snapshot summaries. The independent visitor-level test retains 371 Ghost and 896 Active visitors and finds a Ghost-minus-Active recency difference of 11.39 days (95% CI 10.27–12.51; Welch t = 20.02; p = 7.52 × 10^-63; Cohen d = 1.71). This association does not establish that inactivity causes the label.

The multiple OLS model uses 43,536 training rows and 17,368 visitor-disjoint test rows. Training R² is 0.355 and test RMSE is 0.870 future sessions/week, close to 0.871 for the sessions-only model. The four-week session coefficient is 0.127 (95% CI 0.106–0.148); views and recency intervals cross zero in the multiple fit. Its 5,927 negative test predictions make it unsuitable as a direct count forecast. The logistic test has 15,470 rows, including 316 Ghost labels (2.04%). It obtains ROC-AUC 0.761 and PR-AUC 0.096 versus a no-skill prevalence of 0.020. At the validation-selected 0.10 threshold, precision is 0.191 and recall 0.057, with 18 true positives and 298 false negatives. This threshold is too insensitive for an operational alert.

The weekly Ghost-rate series has 12 mature points. A last-mature-value baseline tested at three historical origins gives MAE 0.00255, RMSE 0.00328 and sMAPE 8.15%. Two future weekly points are displayed at about 3.24%, without an interval. The small backtest cannot establish long-horizon forecast reliability.

The full-feature selected XGBoost plus Platt model reaches test PR-AUC 0.928 (95% visitor-bootstrap CI 0.887–0.958), ROC-AUC 0.970 and Brier 0.059. The test Ghost/Active prevalence is 0.254. The EDS rule reaches PR-AUC 0.802, random forest 0.929, the shared-split Decision Tree 0.927, and Gaussian NB 0.667. The overlapping top-model intervals do not distinguish the tree methods reliably. At threshold 0.05, XGBoost catches all 109 test Ghost rows and has 74 false alerts: precision 0.596 and recall 1.000. About 43% of the test rows are flagged, and medium/high bands coincide under this cost rule.

The named-component ablation still achieves XGBoost PR-AUC 0.909 because overlapping history counts retain baseline information. The observation-only ablation drops to 0.607; observation-only logistic reaches 0.613. This is the main limitation of the headline 0.928 score: it predicts the proposed relative label partly through the baseline that defines that label. It does not demonstrate an equally strong independent early-warning signal.

| Shared test comparison | PR-AUC | Interpretation |
| --- | ---: | --- |
| No-skill prevalence | 0.254 | Ghost fraction in test |
| EDS rule | 0.802 | Prespecified behavioral score |
| Gaussian NB | 0.667 | Independent baseline model |
| Decision Tree | 0.927 | Independent baseline model |
| XGBoost + Platt | 0.928 | Selected on validation |

The tree and XGBoost point estimates are close; their overlap does not establish a winner. The 0.05 operating threshold is tied to an unapproved five-to-one false-negative cost. Because alert prevalence is high, a practical review would need a capacity constraint, an external utility estimate, and calibration on later traffic. None is available in this source.

## VII Discussion and System Demonstration

The web application connects a Next.js interface to seven FastAPI research routes: overview, customers, customer detail, statistics, forecast, prediction and model metrics. The real-data local smoke verified all seven, matched model and data hashes, and checked 404 for unknown IDs and 422 for invalid dates. The dashboard labels the proposed cohort and distinguishes the total snapshot denominator from the ML Ghost/Active test denominator. On a clean machine, `python -m scripts.prepare_real_demo` rebuilds ignored local data and the model before the API and frontend start.

The project can demonstrate an auditable analysis workflow and a working prediction interface. It cannot show that a score is a verified churn probability, that an intervention would work, or that the method generalizes to contemporary traffic. The dataset is from 2015, the Ghost threshold is operational, and only 430 test rows and 12 mature forecast weeks are available. The main full-model performance is sensitive to baseline history. The current cost ratio and score bands need review before real decisions.

The STAT3013 outline also lists SEM. No latent construct or validated measurement indicators have been specified for this event log. We report no SEM fit index or path coefficient. Lecturer guidance is required to determine whether a justified omission is acceptable or whether a new measurement study is needed. This paper remains a review draft until that decision, D-01 through D-05, and the academic integrity checks are completed.

## VIII Conclusion

The verified source supports a reproducible research prototype. One-visitor inference finds a large association between recency and the proposed Ghost label; regression reveals both explanatory signal and poor fit for count decisions; the short time series supports a naive forecast only. Full-history classification ranks the proposed label well, while the observation-only test shows a major reduction in performance. The defensible conclusion is that baseline-relative behavior can be modeled on this cohort, with substantial construct and generalization limits. Future work needs validated outcomes, longer follow-up, a reviewed cohort and cost policy, and an intervention study before any automated retention program.

## References

[1] S. A. Neslin et al., “Defection Detection: Measuring and Understanding the Predictive Accuracy of Customer Churn Models,” Journal of Marketing Research, 2006, doi:10.1509/jmkr.43.2.204.

[2] J. Burez and D. Van den Poel, “Handling class imbalance in customer churn prediction,” Expert Systems with Applications, 2009, doi:10.1016/j.eswa.2008.05.027.

[3] T. Saito and M. Rehmsmeier, “The Precision-Recall Plot Is More Informative than the ROC Plot When Evaluating Binary Classifiers on Imbalanced Datasets,” PLOS ONE, 2015, doi:10.1371/journal.pone.0118432.

[4] C. Guo et al., “On Calibration of Modern Neural Networks,” ICML, 2017, <https://proceedings.mlr.press/v70/guo17a.html>.

[5] S. M. Lundberg and S.-I. Lee, “A Unified Approach to Interpreting Model Predictions,” NeurIPS, 2017, <https://proceedings.neurips.cc/paper_files/paper/2017/hash/8a20a8621978632d76c43dfd28b67767-Abstract.html>.

[6] Retailrocket, “Retailrocket recommender system dataset,” Kaggle, version 2, <https://www.kaggle.com/datasets/retailrocket/ecommerce-dataset>.
