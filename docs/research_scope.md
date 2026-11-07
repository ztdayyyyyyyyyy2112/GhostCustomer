# Research scope — working draft

## Objective and unit of analysis

Study whether behavior observed through snapshot time **T** can identify customers whose future engagement declines while some activity remains. The primary unit is a visitor at a dated snapshot. Multiple snapshots for one visitor are dependent observations. The dashboard demonstrates the analysis; it is not evidence of model performance.

Retailrocket event data is the first dataset to audit. Its suitability, permitted use, observation length, and eligible cohort remain open until the data audit. A longer multi-month event dataset is a fallback if too few visitors have usable history. “Ghost” is an operational future-behavior label, not verified churn or a psychological state.

## Research questions and planned evidence

| ID | Question | Variables and planned analysis | Owner |
| --- | --- | --- | --- |
| RQ1 | How do pre-T engagement patterns differ between future ghost and active groups? | Pre-T sessions, views, carts, purchases, recency, decay; group counts and distributions, a confidence interval for the difference, Welch or rank-based test as appropriate, effect size. Check independence and missingness. | Lâm; Thành presents results |
| RQ2 | Which pre-T signals are associated with future disengagement? | Logistic regression with future ghost label; odds ratios, 95% CIs, p-values, collinearity and calibration checks. Association is not causation. | Long; Lâm prepares features |
| RQ3 | Can a model identify future ghost cases better than simple baselines? | Majority and rule-based baselines versus logistic, RF and optional boosting. Temporal train/validation/test split; PR-AUC, precision, recall, F1 and calibration with class support. | Kiệt; Long integrates inference |
| RQ4 | Can the weekly eligible-cohort ghost rate be forecast at a useful horizon? | Weekly numerator/denominator with fully observable future labels; compare naive baseline with ARIMA only if the series is long enough. Temporal holdout and MAE/RMSE/sMAPE. | Long; Thành presents forecast |

Working hypotheses for RQ1/RQ2: lower recent activity, longer recency, and steeper pre-T decline may be associated with higher future ghost probability. These are hypotheses to test, not findings. Final feature definitions, hypotheses, test families, and any multiple-testing adjustment will be logged before reporting results.

## Time boundary and labels

Features use events at or before T. A confirmation horizon after T defines the future label; rows without a fully observable horizon are `unknown` and excluded from supervised evaluation. Candidate window configurations such as 4+2+2 and 4+3+2 weeks are audit scenarios only. Do not select a window, decline threshold, or session-gap rule until cohort counts, class balance, right-censoring, and sensitivity have been inspected. Do not construct a label from the same pre-T features used to predict it.

Split by time and prevent overlap leakage across snapshots from the same visitor. Fit imputers and scalers on training data only. For inferential tests using repeated snapshots, select an independent visitor-level sample or use clustered standard errors.

## Baselines and limits

Use an all-majority classifier and a simple engagement-decay rule as predictive baselines; use last-observation forecasting as the time-series baseline. Dataset selection, short histories, operational labels, observational associations, and right-censoring limit interpretation. No model score, p-value, confidence interval, or business impact is claimed until the pipeline produces it. SEM is pending clarification of the course requirement and availability of valid latent-construct measurements.

## Deliverables and evidence

Lâm supplies dataset provenance, cohort coverage, dictionary, and label sensitivity. Long supplies statistical tests, regression diagnostics, forecast, and backend responses. Kiệt supplies leakage checks, model comparison, calibration, and inference. Thành keeps the decision log and API contract, builds the frontend, and checks that the report, paper, slides, and demo cite the same reproducible outputs.
