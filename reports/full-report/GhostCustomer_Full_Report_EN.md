# Ghost Customer Prediction from E Commerce Event Histories

STAT3013 full project report, 20 November 2026. The statistical setting is a **proposed** operational definition. All reported numerical results were reproduced from the pinned Retailrocket event file on the local demo machine. The report documents the completed research prototype and its unresolved scientific decisions; it does not claim lecturer approval, a completed SEM analysis, or completed academic integrity checks.

## Abstract

We study whether recent visitor behavior in an e-commerce event log can identify a later decline in engagement. We construct a weekly visitor snapshot with features measured before time T and a future operational Ghost label based on a visitor's own baseline session rate. The verified Retailrocket file contains 2,756,101 events. The proposed 4+2+2-week setting yields 97,489 history-eligible snapshots, of which 85,899 have a fully observed future horizon. Descriptive and visitor-level inferential analyses show higher pre-T recency for Ghost than Active visitors. An OLS regression describes future sessions per week; a separate logistic regression examines Ghost against all other mature states. A 12-week mature Ghost-rate series supports a short naive forecast, but does not support a defensible ARIMA selection. A visitor-disjoint temporal classifier reaches test PR-AUC 0.928 for the proposed Ghost-versus-Active task; when limited to observation-period counts, PR-AUC falls to 0.607. This large reduction shows that baseline history is central to the full model's score. The web demo serves the processed data and trained model through seven real API routes. The work demonstrates a reproducible analytic pipeline; it does not establish true churn, causal effects, or a production-ready intervention policy.

**Keywords:** customer engagement, operational Ghost label, temporal validation, class imbalance, statistical inference, forecasting, machine learning.

## 1 Introduction

### 1.1 Background and research problem

Digital commerce logs record visits, views, cart actions, and transactions, but a silent visitor does not supply a direct statement of intent. A decline in activity may indicate reduced interest, a temporary pause, or the end of a one-time task. We therefore study a measurable future behavior rather than treating the word Ghost as a verified customer state. At each Monday snapshot T, we ask whether the following confirmation period has low activity relative to that visitor's earlier baseline.

The project has four research questions. RQ1 asks how behavior observed before T differs between visitors later assigned Ghost and Active labels. RQ2 asks which pre-T variables are associated with future activity and with a binary Ghost outcome under explicitly different analysis populations. RQ3 asks whether predictive models rank future Ghost versus Active snapshots better than simple baselines on later, visitor-disjoint data. RQ4 asks whether the weekly proportion of known mature Ghost labels can be forecast with evidence appropriate to the available series length.

The practical objective is a transparent research prototype. The application must show exactly what the data and model artifacts contain, preserve missing or censored states, and explain evaluation context. It must not imply that a high score proves abandonment or that contacting a visitor would improve outcomes. The project requirements also list structural equation modeling (SEM). This event-log study currently lacks a justified latent-variable measurement design; Section 7 records that limitation and the question requiring lecturer clarification.

### 1.2 Objectives and contributions

The project contributes a pinned, auditable event-log pipeline, a transparent operational Ghost definition, several statistical tasks with clearly separated analysis populations, and a web demonstration that serves the resulting artifacts. Its methodological contribution is the explicit temporal availability rule: a feature belongs to the period before a prediction time T, whereas a label requires a fully observed later horizon. A visitor may appear at several weekly snapshots, so the report states when repeated rows are descriptive units and when one visitor or a visitor-disjoint split is required. These design choices are integral to the claims, not optional implementation details.

The first objective is to quantify which parts of the public log support a longitudinal cohort after historical eligibility and right censoring. The second is to compare pre-T behavior in operational Ghost and Active groups, with an inferential analysis whose unit is a visitor. The third is to fit and interpret continuous and binary regressions while checking response and error assumptions. The fourth is to evaluate a weekly Ghost-rate forecast only to the extent the mature history permits. The fifth is to compare several classifiers on a shared later test set, inspect calibration and threshold behavior, and measure sensitivity to the baseline variables used in the label. The final objective is to expose the outputs in an end-to-end research interface without filling missing values with mock scientific results.

### 1.3 Scope and evidence boundary

The unit called a “customer” in the interface is an anonymous Retailrocket visitor ID, not an authenticated person. The work is a study of observed interaction events from one historical site and a proposed relative-activity rule. It cannot determine customer intention, explain why engagement fell, or estimate whether a promotion would prevent churn. All model scores must be interpreted as estimates for the operational task under the chosen cohort and split. The dataset cannot validate a satisfaction construct for SEM, and its short mature weekly series cannot support a stable ARIMA choice. Those limitations determine the analysis rather than being hidden as an afterthought.

## 2 Related work and methodological position

### 2.1 Churn prediction and class imbalance

Neslin and colleagues [1] compared predictive accuracy of churn models on validation data. Their study motivates a common held-out comparison, but its outcome and business context differ from this operational event-log label. Burez and Van den Poel [2] studied class imbalance in customer churn prediction. Here the balance changes sharply with the denominator: Ghost is 2.7% of all displayed snapshots, 2.0% of the logistic test sample, and 25.4% of the Ghost-versus-Active ML test sample. Those are three different tasks and cannot share one unqualified prevalence claim.

Saito and Rehmsmeier [3] explain why precision-recall analysis is useful when the positive class is uncommon. We report PR-AUC with support and prevalence alongside ROC-AUC, precision, recall, and threshold. Guo and colleagues [4] discuss probability calibration. We check Brier score and calibration bins rather than assuming that good ranking yields reliable probabilities. Lundberg and Lee [5] introduced SHAP as a model attribution framework. We use attribution to describe fitted model behavior, not to identify causes or a customer’s reasons for inactivity.

No cited study validates the Ghost threshold for this dataset. The definition, session gap, windows, and split were selected for audit feasibility and remain open research decisions D-01 through D-05. The strongest methodological constraint is temporal: every feature must be observed before T, while a label requires the entire future confirmation interval. The second constraint is repeated visitors. We account for them differently by analysis: descriptive tables retain repeated snapshots and disclose dependence; the primary test uses one snapshot per visitor; model test partitions are visitor-disjoint.

### 2.2 Calibration, explanation, and the study gap

The literature supports evaluation principles rather than this exact outcome. A churn model can be compared fairly only after its target, population, time horizon, and costs have been specified. In this project the target is derived from the same event log used as input. The positive fraction ranges from approximately 2% to 25% across the regression and classification tasks because the reference class and split differ. Average precision therefore appears beside each task's support and prevalence. A high ROC-AUC alone would not reveal the number of false alerts at the selected threshold.

Probability calibration asks whether a numerical score corresponds to observed frequency under the test task. It does not turn an operational proxy into a verified churn probability. Likewise, a SHAP or permutation ranking describes which observed variables the fitted model uses, while correlated historical windows can share or exchange attribution. The most important gap in this work is therefore construct dependence: the Ghost label is a future-to-baseline ratio, and the full model sees past baseline activity. We explicitly compare a full model with restricted inputs to measure how strongly the impressive ranking depends on that design choice. This makes the project more useful than a score-only comparison, while keeping its conclusions narrower than real-world customer abandonment.

## 3 Data provenance and audit

### 3.1 Source integrity and event schema

The source is Retailrocket's public e-commerce dataset, Kaggle version 2 [6]. We extracted `events.csv` locally, verified its size of 94,237,913 bytes and SHA-256 `3745aa83238b1e6d44d8fda209807899f420084398f94ddf745f3cbcfecbf9e7`, and counted 2,756,101 events. The source field `visitorid` is an anonymous identifier, not a verified person or account. The processing code retains and flags exact duplicates; the documented duplicate-exclusion sensitivity changes little under the proposed label, but does not prove all anomalous behavior harmless. The source page identifies a CC BY-NC-SA 4.0 license. Raw and visitor-level processed files are excluded from Git.

[[TABLE:source_fields]]

The event file contains a millisecond timestamp, a visitor identifier, an event category, an item identifier and a transaction identifier when relevant. The analysis uses event occurrence and timing; it does not derive customer revenue or lifetime value because `events.csv` does not by itself establish an item price at the moment of every event. Item-property and category data are outside the present pinned analysis. This scope prevents a monetary interpretation that the implemented data join cannot support.

Event timestamps are milliseconds converted to UTC. A session begins after a 30-minute inactivity gap in the proposed setup. Weekly bins begin Monday at 00:00 UTC. The observation boundary is 14 September 2015. A candidate snapshot needs at least five prior events, two active history weeks, and baseline activity. The `audit_compat` cohort keeps historical eligibility visible; the stricter `research` eligibility also requires observation-period activity and is recorded separately in the cohort-flow output. No scientific decision has yet designated one as final.

### 3.2 Snapshot construction and temporal availability

[[FIG:study_design]]

Each eligible visitor may contribute more than one Monday snapshot. This is deliberate: a longitudinal research interface needs to show how an individual's activity changes as the cutoff moves. The same design also creates dependence among rows, because adjacent snapshots reuse much of the same history. Descriptive counts in this report refer to snapshots unless explicitly labeled as distinct visitors; no snapshot count is presented as a count of people. For inference, the primary comparison uses one latest mature row per visitor. For predictive evaluation, a visitor ID may enter only one train, validation, or test partition. Those safeguards answer different statistical questions and should not be conflated.

At a snapshot T, the baseline covers four earlier weeks and the observation window covers the two weeks immediately before T. Feature columns may summarize shorter or overlapping windows within that past. The two-week confirmation window after T is used solely to assign later labels. An outcome remains unknown when any required part of this future interval lies beyond observed data. The feature timestamp audit checks that the most recent source event used for a feature does not extend beyond T. A label-delay purge additionally prevents a training outcome from overlapping the start of validation or a validation outcome from overlapping the start of test. Together these rules remove avoidable temporal leakage, while the operational definition itself still needs scientific review.

For the proposed 4+2+2 windows, baseline covers four weeks, observation the next two weeks, and confirmation the next two weeks. Across 14 snapshot dates, 97,489 rows satisfy the history rule, corresponding to 27,327 distinct visitor IDs. Of those rows, 85,899 have a mature two-week label and 11,590 are right-censored. The mature labels comprise 71,301 Inactive, 9,263 Active, 2,716 Recovered, and 2,619 Ghost snapshots. Display status `candidate` is a subset of immature/unknown operational rows and should not be added to the mature label counts.

[[FIG:cohort_status]]

[[TABLE:cohort_status]]

The label uses sessions per week. If the confirmation rate divided by the baseline rate is below θ = 0.5 and there are future events, the row is Ghost. If future events are zero, it is Inactive. An observation-period decline followed by recovery is Recovered. A fully observed row without those conditions is Active. Immature future horizons are Unknown, with a null target. This is a behavioral proxy. It does not measure true churn or motivation.

### 3.3 Label sensitivity and censoring

Window and label sensitivity matter. The alternative 4+3+2 setting gives 100,140 history-eligible snapshots and 13,511 censored rows. The 6+2+4 setting gives 128,323 history-eligible rows but 40,043 censored rows, showing the coverage cost of a longer confirmation period. Under the current session label, changing θ from 0.5 to 0.4 or 0.3 changes the Ghost count from 2,619 to 1,740 or 1,188. A 15/30/60-minute session gap yields 2,998/2,619/2,310 Ghost rows. These counts are sensitivity evidence, not prevalence estimates for an external population. The exact inputs and flow are in E-01 and E-02.

[[TABLE:sensitivity]]

The alternatives demonstrate why a large raw cohort is not necessarily a stronger supervised experiment. Longer confirmation periods increase the share of candidate rows whose outcomes have not matured by the source boundary. A threshold change can alter both the positive class and the interpretability of the problem, while a session-gap change alters the rate used in that threshold. No result here identifies a unique business-correct value. The current settings provide a reproducible working scenario, and the decision log explicitly leaves final selection open for team and lecturer review. Treating censored rows as negative would bias every late-week rate downward and inflate negative support, so the pipeline keeps a null target for those rows.

## 4 Descriptive statistics and visitor-level inference

### 4.1 Snapshot-level descriptive results

The processed descriptive table has 28 group/metric combinations: four mature label groups by seven features (sessions, views, carts, purchases, active days, recency, and decay ratio). Every row records observed N, missing count/rate, mean, sample standard deviation, quartiles, range, and a histogram. Repeated visitor snapshots remain in these descriptive groups. For example, the 2,619 mature Ghost snapshots have mean four-week sessions 9.19 and mean recency 10.94 days; the 9,263 Active snapshots have corresponding means 8.08 sessions and 4.90 days. These are snapshot-level descriptions. The single missing decay-ratio value among Inactive rows illustrates why missingness is shown explicitly rather than silently imputed.

[[TABLE:descriptive]]

The mean and median should be read together because event intensity has a long right tail. A small set of highly active visitors can raise the mean while the median remains near the low end of the distribution. Zero cart and purchase counts are common. The full seven-feature table therefore reports quartiles and missingness instead of relying on a single average. The group status is assigned using the future confirmation interval, while every displayed feature was measured before T. A snapshot-level comparison is useful for describing the population shown by the dashboard, but it is not an independent-sample test when a visitor appears repeatedly.

### 4.2 Visitor-level hypothesis test

We pre-specified a two-sided comparison of mean pre-T recency between Ghost and Active operational groups. To avoid treating repeated snapshots as independent, we choose each visitor's latest mature snapshot before selecting Ghost or Active rows. This leaves 371 Ghost and 896 Active visitors. We use a Welch t test and a 95% Welch confidence interval for the mean difference; Cohen's d describes standardized size. The Ghost mean is 16.54 days and the Active mean is 5.14 days. The Ghost-minus-Active difference is 11.39 days [10.27, 12.51], t = 20.02 with approximately 414 degrees of freedom, p = 7.52 × 10^-63, d = 1.71. The Ghost share among these 1,267 selected visitors is 0.293 with Wilson 95% interval [0.268, 0.318].

[[FIG:visitor_recency]]

[[TABLE:inference]]

The test assumes visitors are independent and that a large-sample mean comparison remains interpretable despite skew. Selecting the latest snapshot and conditioning on a future label can induce selection effects. The descriptive and inferential means differ because they use different units and inclusion rules. Neither the small p-value nor d establishes a cause or an intervention effect. The full hypothesis, sample, assumptions, and input hashes are in E-04.

The null hypothesis is equality of mean pre-T recency between the two selected visitor groups; the alternative is a two-sided difference. Welch's test does not require equal group variances. The resulting interval is expressed in days, which makes it more interpretable than the p-value alone. Cohen's d standardizes the contrast but does not correct cohort selection. The Wilson interval applies only to the selected mature Ghost/Active visitor set; it should not be called the Ghost rate among all 27,327 visitor IDs or all 97,489 snapshots. These sample definitions are preserved in the API's result metadata so the frontend does not silently mix denominators.

## 5 Regression analysis

### 5.1 Continuous future engagement

The OLS response is the number of sessions in the two-week confirmation interval divided by two, measured in sessions per week. Predictors are four-week pre-T sessions, four-week views, and recency days. The model includes only mature outcomes, checks that each feature timestamp precedes T, and separates a later test period from training. Train outcomes end no later than 3 August 2015; test snapshots begin 17 August. Test visitors observed in training are removed. This leaves 43,536 training rows from 15,689 visitors and 17,368 test rows.

The multiple OLS fit has training R² = 0.355 and test RMSE = 0.870 sessions/week; a one-predictor sessions-only fit has test RMSE = 0.871. Clustered covariance accounts for repeated training visitors. The `sessions_4w` coefficient is 0.127 [0.106, 0.148] sessions/week per prior session. The views and recency coefficients have intervals crossing zero after adjustment. VIF values are below 1.6 for these predictors. The multiple fit produces 5,927 negative predictions on the held-out set, which cannot represent a count. This is a methodological limitation: OLS is an explanatory comparison, not the production forecast of session counts. A count or hurdle model would be a stronger follow-up.

[[TABLE:ols]]

[[FIG:ols_residuals]]

The outcome is nonnegative, skewed and often close to zero, whereas an unconstrained linear model can predict any real number. The negative predictions are therefore a direct model-compatibility failure, not an error to hide by clipping after evaluation. The one-predictor benchmark is nearly as accurate on held-out RMSE, so the additional predictors do not provide a material gain for this particular response. Clustered covariance addresses the uncertainty of coefficients when training snapshots repeat a visitor, but it does not repair the response distribution or identify causal effects. Diagnostic plots and variance inflation factors are supplied to make these conditions visible. A future Poisson, negative-binomial or hurdle comparison would need checks for overdispersion and excess zeros before adoption.

### 5.2 Binary Ghost inference

The separate logistic model uses Ghost = 1 versus all other mature statuses = 0. It includes prior four-week sessions, pre-T recency, and the observation-minus-baseline change in sessions per week. The temporal split purges any training label ending after the validation start and any validation label ending after the test start, then removes visitors seen in earlier partitions. The fitted coefficients use cluster-robust covariance when visitors repeat in training. This sample is deliberately different from the Ghost-versus-Active ML classification task.

The logistic test has 15,470 rows and 316 Ghost labels (prevalence 0.0204). ROC-AUC is 0.761 and PR-AUC is 0.0964, above the no-skill prevalence 0.0204. The validation-selected 0.10 threshold yields precision 0.191 and recall 0.057: 18 true positives, 76 false positives, and 298 missed Ghost rows. This operating point is too insensitive for a practical warning service. Coefficients and odds ratios describe conditional associations under this operational label. They do not justify a causal conclusion. E-05 contains both regression outputs, residual diagnostics, and input hashes.

[[TABLE:logit]]

[[FIG:logit_roc_pr]]

The logistic task includes Inactive and Recovered as negatives, unlike the primary classifier that compares Ghost only with Active. Its coefficient signs must therefore be interpreted conditionally in a different population, not compared directly with the Ghost/Active descriptive means. The temporal train, validation and test construction purges labels whose confirmation interval overlaps a later partition and removes repeated visitors across partitions. This reduces the sample but better reflects the chronology of information availability. Its selected threshold was chosen on validation F1. Low recall on the later test shows that an above-prevalence PR-AUC can coexist with a poor practical alerting point. No claim of production utility follows from the odds ratios alone.

## 6 Weekly forecasting

For each Monday T, the weekly series divides known Ghost labels by known mature Active/Ghost/Recovered/Inactive labels in that bin. Unknown and immature bins are not set to zero. The preparation step finds 12 mature weekly points and no missing Mondays. At each historical forecast origin, only labels whose confirmation interval ended strictly before that origin are available. This label delay is essential; using a rate whose future window overlaps the origin would leak information.

The 12-point series cannot support the code's ARIMA candidate selection criterion of at least 40 weeks and a separate validation segment. We therefore evaluate a naive last-available-mature-rate method at three historical origins. Its holdout MAE is 0.00255 (0.255 percentage points), RMSE 0.00328, and sMAPE 8.15%. The two displayed future weeks use the last mature rate, approximately 3.24%. No interval is provided because the naive rule has no justified predictive interval here. This baseline is a reproducible RQ4 result with weak generalizability, not evidence of a reliable long-range forecast. A longer, consistently labeled time series would be required for ARIMA or seasonality assessment.

[[FIG:weekly_forecast]]

[[TABLE:forecast]]

The forecast origin requires particular care. The weekly rate associated with a snapshot is computed only after its two-week confirmation horizon ends. At an origin, the latest calendar-week observation is not necessarily the latest *known* rate. The backtest admits only rows with `label_end` strictly before the origin and then carries the last mature rate across the resulting delay gap. This avoids using information that would not yet have existed in a real forecast. Three historical origins are enough to exercise the rule and give a transparent error estimate, but not enough to infer a seasonality pattern or stable distribution of errors. The unchanging two-week displayed prediction is a consequence of the naive method and should not be mistaken for a stable business process.

## 7 Structural equation modeling status

The STAT3013 outline lists SEM. An SEM result requires a substantive model of latent constructs, identified indicators, measurement quality, and an estimator appropriate to the variables. The available event log has behavioral counts and derived ratios, but no validated satisfaction or attitude measures and no pre-specified latent measurement model. Fitting an arbitrary diagram to those columns would not answer the outline's example question about satisfaction. We therefore report **no SEM coefficient, fit index, RMSEA, or path diagram**. `docs/sem_feasibility.md` records viable questions for the lecturer. If SEM is mandatory, the study needs a defensible model and data before submission; if a justified omission is allowed, the lecturer's decision must be recorded as D-07/E-09. No approval is presumed here.

An SEM path diagram would imply that observed variables measure particular latent constructs and that the direction of each structural relation has a substantive basis. Counts of views, carts and sessions are not automatically validated indicators of satisfaction or customer intention. Reusing the same derived activity measures as both latent indicators and outcomes would invite identification and interpretation problems. The course requirement can be satisfied only through a lecturer-approved scope decision or additional suitable measurement data and a justified model. The report keeps this section explicit so that a reader does not mistake an omitted result for a zero or a failed model. No synthetic questionnaire or invented fit statistic has been inserted to fill the gap.

## 8 Machine learning prediction of the operational Ghost label

### 8.1 Task population and temporal split

The primary supervised task is Ghost versus Active among fully mature rows. Inactive, Recovered, and Unknown rows are excluded from this model comparison. Every candidate uses the same pre-T feature matrix and visitor-disjoint temporal split. The split first chooses later weeks for validation and test, purges labels overlapping subsequent starts, and assigns visitors to only one partition. Preprocessing, including imputation and calibration, is trained without test data. Hyperparameters and the served family are selected using validation PR-AUC; the operating threshold is selected using validation costs, with a stated false-negative cost of five and false-positive cost of one.

The split retains 2,214 training rows (433 Ghost), 454 validation rows (119 Ghost), and 430 test rows (109 Ghost). Its test prevalence is 0.254. The selected XGBoost plus Platt model has test PR-AUC 0.928 [0.887, 0.958] by 500 visitor-bootstrap resamples; ROC-AUC 0.970 and Brier 0.059. The EDS rule reaches PR-AUC 0.802, logistic regression 0.899, random forest 0.929, and the majority no-skill baseline 0.254. Thành's Decision Tree and Lâm's Gaussian NB were rerun from the same local `modeling_snapshots.csv`: test PR-AUC 0.927 and 0.667. Overlapping confidence intervals do not establish that XGBoost outperforms random forest or Decision Tree. The validation result, not test ranking, determined the served model.

[[TABLE:ml_split]]

### 8.2 Shared test comparison and operating threshold

[[FIG:benchmark_pr_auc]]

[[TABLE:models]]

At the validation-selected threshold 0.05, the selected model catches all 109 Ghost rows in the 430-row test set, with 74 false positives: precision 0.596, recall 1.000, and F1 0.747. About 43% of rows are alerted. This threshold depends on an unapproved cost ratio and makes medium and high bands coincide. It is suitable for a transparent demo, not for an automatic retention action.

[[FIG:model_pr_roc]]

[[FIG:model_confusion_matrix]]

The threshold comes from an illustrative false-negative cost five times a false-positive cost. These are not measured merchant costs, and the chosen cutoff would generate a substantial review burden. A ranking score and an operational decision rule answer different questions: PR-AUC assesses ordering over possible thresholds, while precision and recall quantify what happens at one threshold. The strong test recall is for the constructed Ghost/Active task only. It does not mean the system finds every genuinely departing customer. Before any use in a business process, an analyst would need an agreed capacity or utility policy, a later external validation period and a separate intervention study.

### 8.3 Calibration, attribution and label dependence

[[FIG:model_calibration]]

The most important sensitivity concerns label circularity. The Ghost rule divides future sessions by baseline sessions/week, and the full feature set includes baseline rate and derived decay features. Omitting the named target components while retaining overlapping six- and two-week counts still yields XGBoost test PR-AUC 0.909 because the baseline can be reconstructed. Restricting inputs to ten one- and two-week observation counts, with no baseline-period counts, lowers PR-AUC to 0.607; the analogous logistic model reaches 0.613. The full model therefore predicts the proposed relative label well, but much of its discriminating information comes from the baseline that helps define that label. A reviewer must not interpret 0.928 as an equally strong baseline-independent signal of disengagement. Global SHAP and permutation views are descriptions of the fitted model, not causal explanations.

[[FIG:ablation_pr_auc]]

[[TABLE:ablation]]

[[FIG:importance]]

Platt calibration is fitted using training out-of-fold predictions and kept only if validation Brier score improves. The reliability plot describes the held-out sample but its high-score bins contain few observations, so it is not a certificate that a displayed percentage transfers to new traffic. Attribution is similarly conditional on a fitted model and correlated features; the importance order may move when overlapping windows are changed. The ablation is the more direct integrity check because it asks how much ranking remains when baseline-period counts cannot be reconstructed. Its decrease of approximately 0.321 PR-AUC points is a central finding and belongs beside the headline model score in any slide or demo.

## 9 Application and reproducibility

### 9.1 Research system and API

[[FIG:architecture]]

The application separates a Next.js frontend, a FastAPI backend, processed research artifacts, and an AI inference runtime. Seven API routes serve overview, paginated customers, dated customer detail, statistics, forecast, predictions, and model metrics. The model binary and feature table are read locally. The prediction path checks that the feature row was created before T; an unknown customer returns 404 and invalid date returns 422. The backend refuses model inference when the artifact is absent rather than making up a score. An explicit fixture mode supports interface development and visibly labels its data as illustrative.

[[TABLE:api]]

The interface is deliberately separated from the source of scientific evidence. It reads already computed aggregates and model artifacts through documented contracts. A dashboard percentage is meaningful only with its own denominator and dataset notice; it is not substituted for a statistical result table. The customer detail route uses both visitor ID and snapshot date because one visitor can appear at multiple Mondays. The prediction route also requires that pair. This prevents an ambiguous lookup from silently mixing features from one date with a label or score from another. API errors are part of the demonstration, not exceptional cases hidden from reviewers.

### 9.2 Demonstration and software checks

[[FIG:dashboard_real]]

On 20 November 2026, the pinned raw file reproduced the feature and label SHA-256 values recorded in the original AI run. The structural checker passed all 97,489 detail files. The real-data smoke exercised all seven API routes, checked the model binary hash against `model_meta.json`, and verified successful prediction plus 404 and 422 errors. Python tests passed 122 cases; frontend lint and real-mode production build passed. Desktop and mobile pages loaded without browser page errors. These checks validate software integration and reproducibility on the local machine. They do not approve the scientific decisions.

[[TABLE:verification]]

The reproducible command sequence is documented in `docs/runbook.md`. A new machine needs the licensed `events.csv` and must run `python -m scripts.prepare_real_demo`; raw and processed customer data and the trained model are not committed. The project should avoid publishing real visitor IDs in screenshots, examples, or repository artifacts. Evidence IDs E-00 through E-11 map report numbers to scripts and aggregate files in `docs/evidence_register.md`.

The demonstration route through the web application is Overview, Customers, dated customer detail, Statistics, Forecast, Predict, and Model Metrics. The interface displays the proposed cohort notice and the model version rather than presenting a score without context. The customer list can be filtered to a Ghost row and the same date carried into prediction. The statistics page gives the visitor-level test alongside descriptive groups, while the forecast page states that its two points come from a naive last-mature-value rule. The model page shows support, prevalence, PR-AUC, calibration and confusion. On a demonstration machine the backend and frontend run locally at ports 8000 and 3000 respectively. The report does not treat a successful browser walkthrough as evidence that the scientific labels are externally valid.

## 10 Discussion and recommendations

### 10.1 Findings by research question

RQ1 finds a large association between pre-T recency and the proposed future Ghost label in the selected independent visitor-level comparison. RQ2 finds that previous session activity helps explain future sessions per week, while the linear model's negative count predictions reveal a poor response distribution fit; the separate logistic model ranks above chance but misses most Ghost cases at its selected threshold. RQ3 finds strong prediction of the relative label with full history, but the observation-only ablation sharply reduces performance. RQ4 produces only a short naive forecast because the number of mature weekly points is small.

These results support a cautious product recommendation: display the score alongside its operational definition, model version, sample support, threshold, and uncertainty. An analyst can use the interface to inspect cohort behavior and generate hypotheses. The current score should not trigger automatic promotions or be treated as a true churn probability. Before any operational trial, the team would need a validated outcome, a cost policy, a more stable temporal test, monitoring under new traffic, and an intervention study that measures benefit and harm. The event log alone does not provide those outcomes.

### 10.2 Decision implications

The strongest usable output today is methodological. A business analyst could use the dashboard to examine whether a proposed relative-activity definition remains stable under a different session rule, threshold, or observation horizon. The score might help prioritize manual investigation within this research cohort, but its threshold would need to be tied to a measured review capacity and false-alert cost. The current five-to-one ratio is an experiment setting, not a merchant policy. A later intervention would require recording which visitors were contacted and comparing outcomes against a valid control group. Without that study, neither an increase in engagement nor a financial return can be attributed to this model.

For the research team, the large difference between full and observation-only PR-AUC is more important than the small ranking gaps among tree methods. It shows that the baseline used in a relative outcome is a substantial source of predictable structure. The team should decide whether the scientific question is to predict the proposed ratio using all available past history, or to detect a new deterioration signal from only the most recent observation window. Both are legitimate but distinct tasks. The report and model card currently present the first as the primary task and the second as a sensitivity analysis. A final submission should record which interpretation the lecturer accepts.

## 11 Limitations and next decisions

The strongest limitation is construct validity: Ghost is defined from relative sessions, not observed customer intent. The dataset is from 2015 and its anonymous IDs may not correspond to durable customers. The cohort excludes many low-history visitors, while repeated snapshots create dependence. The 4+2+2 choice is sensitive to session gap, threshold, and confirmation duration. The full model's high PR-AUC depends strongly on baseline history. The classification test has only 430 rows; the weekly forecast has 12 points and three holdout origins. The naive forecast has no interval. OLS gives negative count predictions, and the logistic decision threshold misses most positives. No result supports a causal claim.

Before calling this a final study, the group must document decisions D-01 through D-05 and review the proposed 4+2+4 sensitivity without mixing its results with 4+2+2. The lecturer must clarify D-07 for SEM. The submission also requires a 7–10-page IEEE paper in the official template, slides, a demo video, Turnitin evidence at or below the required similarity threshold, an AI-generation audit and explanation, and working course-system links. This AI-assisted report requires human editing, citation verification, and audit disclosure.

### 11.1 Internal and external validity

The operational Ghost rule is sensitive to session inference, eligible history and the confirmation ratio. Training and test labels come from the same site and historical period, so performance on this held-out task does not establish portability to a new store, current devices, different product categories or different identity tracking. Visitor IDs may not correspond to durable people, and a silent period has several possible explanations. The history rule also excludes many low-activity visitors, limiting the population to which the model could be applied. Temporal and visitor-disjoint evaluation reduces two important leakages but cannot remove a mismatch between the constructed outcome and true customer intent.

### 11.2 Academic and deployment decisions

Several course requirements are outside what repository code can verify. A lecturer must determine whether the SEM requirement permits a documented omission on an event-log dataset or calls for a separate measurement study. The instructor or team must approve the final cohort, label threshold, window design and split before describing the results as final. The institutional submission system, similarity checker and AI-content checker require authenticated human access. The report records their status without inventing screenshots or approvals. A narrated demo video and final class/group repository naming convention also require team-specific information. These are explicit completion items, not missing values to be filled with fictional evidence.

## 12 Conclusion

The project now runs end to end on a verified public event file. Its statistical tests, regressions, forecast baseline, classification comparisons, and web demo can be reproduced locally. The most defensible scientific result is narrower than a product claim: historical baseline activity helps predict the group's relative Ghost rule, but a model restricted to recent observation activity is substantially weaker. The application is ready for a transparent research demonstration, with research approvals and submission evidence still open.

## References

[1] S. A. Neslin et al., “Defection Detection: Measuring and Understanding the Predictive Accuracy of Customer Churn Models,” Journal of Marketing Research, vol. 43, no. 2, 2006, doi:10.1509/jmkr.43.2.204.

[2] J. Burez and D. Van den Poel, “Handling class imbalance in customer churn prediction,” Expert Systems with Applications, 2009, doi:10.1016/j.eswa.2008.05.027.

[3] T. Saito and M. Rehmsmeier, “The Precision-Recall Plot Is More Informative than the ROC Plot When Evaluating Binary Classifiers on Imbalanced Datasets,” PLOS ONE, 2015, doi:10.1371/journal.pone.0118432.

[4] C. Guo et al., “On Calibration of Modern Neural Networks,” Proceedings of ICML, 2017, <https://proceedings.mlr.press/v70/guo17a.html>.

[5] S. M. Lundberg and S.-I. Lee, “A Unified Approach to Interpreting Model Predictions,” NeurIPS, 2017, <https://proceedings.neurips.cc/paper_files/paper/2017/hash/8a20a8621978632d76c43dfd28b67767-Abstract.html>.

[6] Retailrocket, “Retailrocket recommender system dataset,” Kaggle, version 2, <https://www.kaggle.com/datasets/retailrocket/ecommerce-dataset>.

[7] STAT3013 course team, “Outline Project STAT3013 2026,” course requirements supplied to the project group, 2026.

## Appendix A Reproduction

The exact raw source SHA-256, scenario parameters, event and label schemas, source license, feature list, data processing commands, split manifest, output hashes, model card, and API contract are stored in `data/config/pipeline.json`, `docs/data_dictionary.md`, `docs/runbook.md`, `ai/evaluation/run_summary.json`, `ai/evaluation/model_meta.json`, `docs/api_contract.md`, and `docs/evidence_register.md`. The local `data/processed/manifest.json` carries hashes of ignored processed artifacts. Figures and tables can be regenerated with `python -m scripts.prepare_real_demo`. The model binary is intentionally not in Git; its SHA-256 is recorded in the model metadata.

### A.1 Required source and environment

Obtain the licensed Retailrocket version 2 archive from the cited dataset page and place its verified `events.csv` in `data/raw/`. The pipeline rejects a different byte count or SHA-256. Use a virtual Python environment with `requirements-defense.txt` and the frontend lockfile with `npm ci`; keep the raw file, visitor-level output and binary model outside Git. Reproduction on a new machine is therefore a controlled build, not a simple clone-and-run shortcut. The code and aggregate outputs in the repository show what should be reproduced, while the raw event file must be acquired from its publisher.

### A.2 Ordered build and verification

Run `python -m scripts.prepare_real_demo` from the repository root. The orchestrator runs the data pipeline, exports sensitivity and detail artifacts, computes the visitor-level test, prepares the forecast series, executes the regressions and diagnostics, trains the ML candidates, reruns the two independent baselines, writes aggregate research files, checks schema integrity and calls the seven real API routes. The final smoke check asserts the model binary SHA-256, the feature and label hashes, a valid score, a 404 for an unknown ID and a 422 for an invalid date. Only after those checks should the FastAPI backend and Next.js frontend be started in real mode. The frontend's `NEXT_PUBLIC_API_MODE` and URL values are build-time settings and should be confirmed before the production build. The step-by-step commands are kept in `docs/runbook.md`.

### A.3 Traceability and interpretation

[[TABLE:evidence]]

The evidence register separates source provenance, cohort audit, descriptive statistics, inference, regressions, forecasting, classification, runtime and integration. Reproducing one file in isolation is not sufficient after a change to the label or windows: all dependent outputs, the web demo, report tables and slide figures must be regenerated together. The design log distinguishes an observed result from an unapproved scientific decision. For this report, a number is considered supported only when it appears in a tracked aggregate artifact or a locally rebuilt file whose input hash is recorded. Screenshots document display behavior but do not replace their numerical source tables.

## Appendix B Contributions and scope

The repo attributes the shared data pipeline and cohort audit to Lâm, the regression and forecasting algorithms and backend foundation to Long, the model training/evaluation and inference package to Kiệt, and the frontend integration, Decision Tree benchmark, current end-to-end reproducibility work, inferential adapter, and defense assembly to Thành. The current rerun of teammates' scripts does not transfer their original authorship. Every member should be able to explain the full design, not only their own module.

[[TABLE:roles]]

The contribution map combines the original division of work with the modules and aggregate artifacts currently in `develop`. It is a project record, not a claim that one person authored every rerun. The final signed report should be checked by all four members, especially where a teammate's model output is interpreted outside its original notebook. The team also needs to confirm class and group codes for the required GitHub repository name and the course instructor's preference for SEM treatment.

## Appendix C Submission evidence status

The repository includes a 12-slide defense deck and a seven-page provisional two-column paper draft. The latter still requires transfer to the official IEEE conference template and a pagination check. A narrated demonstration video, Turnitin similarity screenshot, AI-generation audit and the course-system upload records are not available in the research artifacts inspected for this report. The course asks for those materials, but recording them as completed without files would be misleading. The software checks and figures in this report support the local technical demonstration; they do not substitute for academic-integrity evidence or lecturer approval.
