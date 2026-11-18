**Run:** `ghost-xgboost-cal-27f274df` · split `visitor-temporal-v1_tr2015-07-06_va2015-07-27_te2015-08-24_f50-25-25_s3013` · label task `ghost_vs_active` (label version `ghost-baseline-ratio-v1-proposed`, scenario `b4_o2_c2`) · generated 2026-11-17T13:38:57Z

**Table ML-1. Visitor-aware temporal split.**

| split | rows | visitors | positives | prevalence | snapshot_min | snapshot_max | label_end_max |
|---|---|---|---|---|---|---|---|
| train | 2214 | 1271 | 433 | 0.196 | 2015-06-15 | 2015-07-06 | 2015-07-20 |
| validation | 454 | 340 | 119 | 0.262 | 2015-07-27 | 2015-08-03 | 2015-08-17 |
| test | 430 | 326 | 109 | 0.254 | 2015-08-24 | 2015-08-31 | 2015-09-14 |

8784 of 11882 supervised rows are not used because of label purging or visitor bucketing.

**Table ML-2. Model comparison (selection on validation PR-AUC; test evaluated once).**

| name | family | val_pr_auc | test_pr_auc | test_pr_auc_ci95 | test_roc_auc | test_recall | test_precision | test_f1 | test_brier | threshold |
|---|---|---|---|---|---|---|---|---|---|---|
| majority | baseline | 0.262 | 0.254 | [0.203, 0.297] | 0.500 | 1.000 | 0.254 | 0.405 | 0.193 | 0.190 |
| rule_eds | baseline | 0.774 | 0.802 | [0.7314, 0.8631] | 0.869 | 0.826 | 0.584 | 0.684 | 0.099 | 0.090 |
| logistic_regression | linear | 0.884 | 0.899 | [0.8512, 0.9373] | 0.955 | 0.917 | 0.606 | 0.730 | 0.071 | 0.140 |
| random_forest | tree | 0.909 | 0.929 | [0.8862, 0.9589] | 0.972 | 1.000 | 0.592 | 0.744 | 0.058 | 0.150 |
| xgboost | boosting | 0.913 | 0.928 | [0.8872, 0.9583] | 0.970 | 1.000 | 0.602 | 0.752 | 0.059 | 0.050 |
| svm_rbf | optional | 0.817 | 0.803 | [0.727, 0.8782] | 0.936 | 1.000 | 0.509 | 0.675 | — | 0.400 |
| isolation_forest | optional | 0.367 | 0.322 | [0.2552, 0.4161] | 0.643 | 0.890 | 0.327 | 0.478 | — | 0.080 |
| xgboost+platt | boosting | 0.913 | 0.928 | [0.8872, 0.9583] | 0.970 | 1.000 | 0.596 | 0.747 | 0.059 | 0.050 |

No-skill PR-AUC equals test prevalence = 0.253. Rank-only models (SVM, Isolation Forest) have no Brier score because their outputs are not probabilities.

**Selected model:** xgboost+platt with {'max_depth': 3, 'min_child_weight': 10}; calibration: {'method': 'Platt on visitor-grouped train out-of-fold scores', 'val_brier_raw': 0.06914, 'val_brier_calibrated': 0.06878, 'applied': True}.

**Operating point (chosen on validation):** threshold 0.05 (min expected cost on validation, C_FN=5.0, C_FP=1.0); risk bands {'high': 0.05, 'medium': 0.05}.

**Test at the operating threshold:** support 430, Ghost 109 (prevalence 0.253), precision 0.596, recall 1.000, F1 0.747, ROC-AUC 0.970, PR-AUC 0.928, Brier 0.059, ECE 0.042; confusion matrix [[TN, FP], [FN, TP]] = [[247, 74], [0, 109]].

**Table ML-3. Circularity ablation (label uses baseline sessions/week).**

| feature_set | model | n_features | val_pr_auc | test_pr_auc | test_roc_auc |
|---|---|---|---|---|---|
| full | xgboost | 41 | 0.913 | 0.928 | 0.970 |
| full | logistic_regression | 41 | 0.884 | 0.899 | 0.955 |
| no_target_components | xgboost | 36 | 0.910 | 0.909 | 0.963 |
| no_target_components | logistic_regression | 36 | 0.877 | 0.885 | 0.945 |
| baseline_only | xgboost | 1 | 0.654 | 0.666 | 0.906 |
| baseline_only | logistic_regression | 1 | 0.516 | 0.492 | 0.847 |

**Table ML-4. Permutation importance on validation (PR-AUC drop).**

| feature | pr_auc_drop_mean | pr_auc_drop_sd |
|---|---|---|
| feature_baseline_sessions_per_week | 0.243 | 0.023 |
| feature_decay_ratio | 0.189 | 0.026 |
| feature_recency_days | 0.008 | 0.005 |
| feature_sessions_6w | 0.004 | 0.003 |
| feature_views_6w | 0.004 | 0.002 |
| feature_views_2w | 0.004 | 0.001 |
| feature_cart_to_view | 0.003 | 0.002 |
| feature_events_6w | 0.003 | 0.001 |
| feature_n_distinct_items_pre | 0.003 | 0.002 |
| feature_sessions_2w | 0.002 | 0.001 |

Explanations: {'permutation': 'validation PR-AUC drop, 10 repeats', 'local': 'baseline replacement (train medians), probability points', 'shap': 'SHAP (TreeExplainer), unit: model margin (log-odds for boosting, probability for forests), n=430 test rows'}. These are associations, not causal effects.
