# 8. Machine-learning prediction of Ghost status (RQ3) — results draft

*Owner: Trần Quốc Kiệt. Method: `ml_methods.md`. Values below come from the 20 November 2026 real-data rerun in `ai/evaluation/` (E-07/E-08). The 4+2+2 window is a proposed setting. A 4+2+4 sensitivity run, if performed, must be reported separately.*

## 8.1 Data used for modeling

The 4+2+2 cohort contains 97,489 visitor-snapshots, of which 11,882 are mature `ghost` or `active` rows used for the primary task (2,619 Ghost, 22.0 %). The visitor-aware temporal split and strict label purging leave 3,098 rows (Table 8.1). The remaining 8,784 rows are excluded because their label window overlaps the next period, or because their visitor belongs to another split. Ghost prevalence rises from 19.6 % in training to 25.4 % in test, which is consistent with the general decline of activity late in the observation period.

**Table 8.1. Visitor-aware temporal split** (`ai/evaluation/split_manifest.json`)

| Split | Snapshots (T) | Rows | Visitors | Ghost | Prevalence |
|---|---|---|---|---|---|
| Train | 15 Jun – 6 Jul 2015 | 2,214 | 1,271 | 433 | 0.196 |
| Validation | 27 Jul – 3 Aug 2015 | 454 | 340 | 119 | 0.262 |
| Test | 24 Aug – 31 Aug 2015 | 430 | 326 | 109 | 0.254 |

No visitor appears in two splits. Each split's label windows end before the next split starts.

## 8.2 Model comparison

Hyper-parameters were chosen on validation PR-AUC. Every model was then scored once on the untouched test split (Table 8.2). The no-skill PR-AUC equals test prevalence, 0.254.

**Table 8.2. Test performance** (`model_comparison.csv`; 95 % CIs from 500 visitor-level bootstrap resamples; precision, recall and F1 at each model's validation-chosen threshold)

| Model | Test PR-AUC [95 % CI] | ROC-AUC | Precision | Recall | F1 | Brier |
|---|---|---|---|---|---|---|
| Majority (prior) | 0.254 [0.203, 0.297] | 0.500 | 0.254 | 1.000 | 0.405 | 0.193 |
| EDS rule | 0.802 [0.731, 0.863] | 0.869 | 0.584 | 0.826 | 0.684 | 0.099 |
| Logistic regression | 0.899 [0.851, 0.937] | 0.955 | 0.606 | 0.917 | 0.730 | 0.071 |
| Random forest | 0.929 [0.886, 0.959] | 0.972 | 0.592 | 1.000 | 0.744 | 0.058 |
| XGBoost | 0.928 [0.887, 0.958] | 0.970 | 0.602 | 1.000 | 0.752 | 0.059 |
| **XGBoost + Platt (selected)** | **0.928 [0.887, 0.958]** | **0.970** | **0.596** | **1.000** | **0.747** | **0.059** |
| RBF-SVM (rank score) | 0.803 [0.727, 0.878] | 0.936 | 0.509 | 1.000 | 0.675 | — |
| Isolation Forest (rank score) | 0.322 [0.255, 0.416] | 0.643 | 0.327 | 0.890 | 0.478 | — |

On the same split, run with the owners' scripts:

| Model | Test PR-AUC | ROC-AUC | Precision | Recall | F1 | Brier |
|---|---|---|---|---|---|---|
| Decision tree (Thành) | 0.927 | 0.973 | 0.629 | 0.963 | 0.761 | 0.080 |
| Gaussian NB (Lâm) | 0.667 | 0.861 | 0.550 | 0.761 | 0.639 | 0.192 |

These two use a fixed 0.5 threshold. Their independent reruns are saved in `research/baselines/decision_tree_results.json` and `research/baselines/gaussian_nb_results.json` on the same split; scientific review of D-02/D-03/D-05 remains open.

Tree ensembles and boosting are the strongest models. Their test PR-AUC is about 0.93, against 0.80 for the single-feature EDS rule and 0.25 for no skill. The CIs of random forest, XGBoost and the decision tree overlap almost completely, so the data do not separate these three. XGBoost was served because it had the highest validation PR-AUC (0.913), not because it is significantly better on test. Isolation Forest, which ignores labels, barely beats chance. "Unusual" visitors are not the same as Ghost visitors.

## 8.3 Calibration and operating threshold

Platt scaling fitted on training out-of-fold scores lowered validation Brier only slightly (0.0691 → 0.0688), but was kept by the pre-registered rule. On test, Brier is 0.059 and the expected calibration error is 0.042 over ten bins (`figures/model_calibration.png`).

The cost rule (missed Ghost = 5, false alert = 1) chose a threshold of 0.05 on validation. At this threshold the test confusion matrix is [[TN 247, FP 74], [FN 0, TP 109]]:

- every test Ghost is caught (recall 1.000);
- 43 % of rows are alerted, so precision is 0.596.

The F1-maximising threshold on validation is 0.48 (`threshold_study.csv`). With this cost ratio the medium band coincides with the high band. This needs revisiting before the dashboard is used for prioritisation.

## 8.4 What drives the score, and the circularity check

Permutation importance on validation (`figures/shap_or_permutation_importance.png`) and mean |SHAP| on test both put two features far ahead of all others:

- `feature_baseline_sessions_per_week`: PR-AUC drop 0.243; mean |SHAP| 1.90;
- `feature_decay_ratio`: PR-AUC drop 0.189; mean |SHAP| 1.18.

The next feature, recency, causes a drop of only 0.008.

The label divides future sessions by the baseline rate, so these features are partly components of the target. Table 8.3 retrains the selected family and logistic regression without them.

**Table 8.3. Circularity ablation** (`ablation.csv`, test PR-AUC)

| Feature set | XGBoost | Logistic |
|---|---|---|
| All 41 features | 0.928 | 0.899 |
| Without baseline rate, decay ratio and EDS (36) | 0.909 | 0.885 |
| Observation-window counts only (10) | 0.607 | 0.613 |
| Baseline rate only (1) | 0.666 | 0.492 |

Performance barely changes without the named label components. However, the baseline rate can still be reconstructed from `feature_sessions_6w − feature_sessions_2w`. The additional observation-only test removes all baseline-period counts and keeps only one- and two-week event/session counts. Its PR-AUC falls to about 0.61, showing that baseline history supplies much of the full model's signal.

The results are consistent with **regression to the mean**: visitors with an unusually active baseline are more likely to fall below half of it afterwards. The 0.928 full-model PR-AUC measures prediction of this operational label; it does not establish an equally strong baseline-independent early warning signal. The observation-only PR-AUC of 0.607 is the stricter check.

## 8.5 Inference service

The selected model (`ghost-xgboost-cal-27f274df`, current local artifact SHA-256 in `ai/evaluation/model_meta.json`) is served by `ai/inference/runtime.py` through `POST /api/predict`. The ID path only reads the pre-T feature row and re-checks `feature_max_event_time_utc < T`. Unknown visitors return 404 and invalid input returns 422. `top_factors` reports the change in score when a feature is set to its training median. This is an association, not a cause.

## 8.6 Answer to RQ3 and limitations

Using only pre-T behaviour, tree-based models rank future Ghost visitors far better than chance or the EDS rule (test PR-AUC 0.93 vs 0.80 and 0.25). Most of that signal comes from how far a visitor's recent baseline sits above their usual level. The result depends on several conditions:

- an operational label;
- a short horizon (12 mature weeks with the 2-week window);
- a small test set (430 rows; CI ±0.04);
- a label that shares inputs with the predictors.

It describes associations in 2015 Retailrocket traffic and does not show that acting on the score changes behaviour.
