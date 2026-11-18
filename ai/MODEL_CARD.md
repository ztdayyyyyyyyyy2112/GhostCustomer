# Model card — Ghost Customer risk score

Status: **pipeline implemented and tested on synthetic data; no real-data result is approved yet.** Fill the "Run" section from `ai/evaluation/run_summary.json` after a real run. Do not edit numbers by hand.

## Intended use

- Rank Retailrocket visitors at a weekly snapshot T by the risk that their engagement in the next confirmation window falls below θ × their own baseline rate (the operational "Ghost" label, `ghost-baseline-ratio-v1-proposed`).
- Course research (STAT3013, RQ3) and the web demo. The demo shows the score next to the evaluation context.
- **Not for:** claims that a visitor has churned or left, causal statements about why, automated actions without human review, or any population other than the Retailrocket cohort it was trained on.

## Data

- Source: Retailrocket e-commerce events (Kaggle v2, CC BY-NC-SA 4.0). Anonymous `visitorid`, 2015-05-04 to 2015-09-14.
- Rows: visitor × weekly snapshot T from Lâm's cohort (scenario `b4_o2_c2`, ≥ 5 pre-T events, ≥ 2 active weeks, baseline activity > 0).
- Features: 41 pre-T `feature_*` columns (windows end strictly before T). IDs, dates, labels, and confirmation-window fields are excluded and checked by code.
- Label task (default): ghost = 1 vs active = 0. Inactive (zero future events), recovered, and unknown/censored rows are excluded. This follows the Decision Tree / Gaussian NB benchmark contract and still needs D-03 approval.

## Training and selection

- Split: visitor-aware temporal split (D-05 proposal). Each visitor belongs to one split. Earlier label windows end before the next split starts. Test is the last mature weeks and is evaluated once.
- Candidates: majority, EDS rule, logistic regression, random forest, gradient boosting (XGBoost or HistGradientBoosting), and optionally SVM / Isolation Forest.
- Hyper-parameters and the served model are chosen on **validation PR-AUC**. Platt calibration is fitted on train out-of-fold scores and kept only if validation Brier improves.
- Operating threshold: minimum expected cost on validation with C_FN = 5, C_FP = 1. This is a business assumption; see `threshold_study.csv` for other operating points.

## Run (fill from a real run)

| Field | Value |
|---|---|
| model_version | _pending real run_ |
| split_version | _pending_ |
| input SHA-256 (features / labels) | _pending_ |
| test support / prevalence | _pending_ |
| test PR-AUC [95 % CI] vs no-skill | _pending_ |
| test ROC-AUC, Brier, ECE | _pending_ |
| operating threshold, precision, recall | _pending_ |
| ablation without target-component features | _pending_ |

## Known limitations

- **Operational proxy label.** "Ghost" is a rule over session counts, not observed churn or intent. Results change with θ, the windows, and the session gap (see E-02).
- **Circularity.** The label divides future sessions by `feature_baseline_sessions_per_week`, which is also an input. `feature_decay_ratio` and `feature_eds` are derived from the same rate. Predictive claims should cite the `no_target_components` ablation.
- **Right-censoring and short horizon.** Only about 12 mature snapshot weeks exist, and strict purging removes 2 weeks at each split boundary. Test sets are small, so the bootstrap CIs are wide.
- **Sample selection.** Only visitors with enough pre-T history are scored. Inactive and recovered visitors are excluded from the default task, but the deployed model still scores them.
- **Repeated snapshots.** Rows from the same visitor are dependent. CIs resample visitors, not rows.
- **Observational data.** Feature attributions and coefficients describe associations. Acting on a high score is not evidence that an intervention helps.
- **Calibration.** Probabilities are calibrated on 2015 Retailrocket data only and drift under any other traffic mix.

## Explanations

`top_factors` in the API is the change in score when one feature is set to its training median (probability points, interactions ignored). Global views: permutation importance on validation, plus SHAP when the `shap` package is installed.

## Ownership

Kiệt (model, split, card), Long (API integration), Lâm (features/labels), Thành (review, Decision Tree benchmark).
