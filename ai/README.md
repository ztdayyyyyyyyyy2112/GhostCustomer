# AI / ML module — Ghost Customer prediction (RQ3)

Owner: Trần Quốc Kiệt. Covers AI-01 … AI-13 in the task plan. All code runs on Lâm's processed tables; nothing here re-labels data.

## Quick start

```bash
python -m pip install -r ai/requirements.txt
python -m pytest ai/tests -q                         # 56 tests, synthetic data, ~1 min

# Dry run with generated events pushed through Lâm's real pipeline functions
python -m ai.training.run --synthetic --optional-models
python -m ai.evaluation.report --dir data/processed/ai_dryrun

# Real run (needs data/processed/customer_features.parquet + customer_labels.parquet)
python -m ai.training.run --optional-models
python -m ai.evaluation.report
```

Synthetic runs always write to `data/processed/ai_dryrun/` (ignored by Git) and are refused for `ai/evaluation/`, so mock numbers can never reach `/api/model/metrics`.

## Pipeline

| Task | Where | What it does |
|---|---|---|
| AI-01 schema | `training/config.py`, `training/data.py` | Loads features + labels, merges on `(visitorid, snapshot_date)`, feature allowlist = `feature_*` minus `feature_max_event_time_utc`; rejects IDs, dates, labels, `future_*`, split fields. |
| AI-02 baselines | `training/models.py` | `majority` (prior) and `rule_eds` (rank by `feature_eds`) benchmarks. |
| AI-03 split | `training/split.py` | Visitor-aware temporal split with strict label purging; writes `split_manifest.json` and `data/processed/modeling_snapshots.csv` for Thành's Decision Tree and Lâm's Gaussian NB (passes their validator). |
| AI-04 preprocessing | `training/preprocess.py` | Inside the sklearn Pipeline, fitted on train only: median imputation + missing indicators, `log1p` for counts/rates, scaling for linear/SVM. |
| AI-05 logistic | `training/models.py` | `LogisticRegression`, `C` × `class_weight` tuned on validation PR-AUC. |
| AI-06 random forest | `training/models.py` | `max_depth` × `min_samples_leaf` × `class_weight`. |
| AI-07 boosting | `training/models.py` | XGBoost when installed, otherwise sklearn `HistGradientBoosting` (recorded in the model name). |
| AI-08 optional | `--optional-models` | RBF-SVM and Isolation Forest as rank-only scores (no Brier / no probability claim). |
| Calibration | `PlattCalibrated` | Sigmoid on visitor-grouped train out-of-fold scores; kept only if validation Brier improves. |
| AI-09 evaluation | `evaluation/metrics.py` | Support, prevalence, P/R/F1 at a stated threshold, ROC-AUC, PR-AUC, Brier, ECE, calibration bins, `[[TN, FP], [FN, TP]]`, visitor-cluster bootstrap 95 % CIs. |
| AI-10 threshold | `evaluation/threshold.py` | Threshold table on validation; operating point = min expected cost (C_FN = 5, C_FP = 1); risk bands. |
| AI-11 explanations | `evaluation/explain.py` | Permutation importance (validation), SHAP if `shap` is installed, baseline-replacement attribution summary, logistic coefficients for comparison with Long's logit. |
| AI-12 inference | `inference/runtime.py` | `predict(payload) -> dict` for `POST /api/predict`. |
| AI-13 handoff | `MODEL_CARD.md`, `evaluation/report.py`, `reports/full-report/ml_methods.md` | Model card, auto-generated result tables, methods text. |

## Outputs of a real run (`ai/evaluation/`)

`metrics.json` (served by `/api/model/metrics`, validated against `ModelMetricsResponse`), `split_manifest.json`, `model_comparison.csv`, `tuning.csv`, `ablation.csv`, `threshold_study.csv`, `permutation_importance.csv`, `attribution_summary.csv`, `shap_importance.csv` (if SHAP), `logistic_coefficients.csv`, `run_summary.json`, `model_meta.json`, `results_tables.md`, `figures/*.png`. The model binary goes to `ai/models/ghost_model.joblib` (ignored; share it with its SHA-256 from `model_meta.json`).

## Inference contract (`ai/inference/runtime.py`)

```python
from ai.inference.runtime import predict
predict({"customer_id": "257597", "snapshot_date": "2015-08-24"})
predict({"features": {"feature_sessions_4w": 3, ..., "feature_eds": None}})   # all allowlisted keys, null allowed
# -> {"score": 0.41, "risk_label": "high", "top_factors": [{"feature": "...", "contribution": 0.08}],
#     "model_version": "ghost-random-forest-cal-1a2b3c4d", "dataset_notice": "..."}
```

| Situation | Exception | API status |
|---|---|---|
| unknown customer / snapshot | `LookupError` | 404 |
| bad date, unknown or missing feature, non-numeric, negative count, all null, both/neither inputs | `ValueError` | 422 |
| model or feature table missing | `RuntimeError` | 503 (fixtures still work in demo mode) |

The ID path reads the row Lâm's pipeline built from events strictly before T and re-checks `feature_max_event_time_utc < T`. `top_factors` = change in score when one feature is set to its training median (probability points). This is an association, not a cause. Override paths with `GHOST_MODEL_PATH` and `GHOST_FEATURES_PATH`.

## Decisions still open

- **D-03 label mapping:** default task `ghost_vs_active` (same rows as the Decision Tree/GNB benchmark). `--label-task ghost_vs_rest` is the sensitivity that keeps inactive/recovered as 0.
- **D-05 split:** proposal = last 2 mature weeks test, 2 weeks validation, strict purge, visitor buckets 50/25/25. `--no-visitor-disjoint` gives a time-only sensitivity run.
- **Feature set:** served model uses `full`; the run always reports the `no_target_components` and `baseline_only` ablation because the label is defined relative to baseline sessions/week.
