# Thành's Decision Tree benchmark

This is Thành's independent algorithm for RQ3. It compares a shallow Decision Tree with an all-majority baseline. It does not change the web API or select the production inference model. No empirical result is committed here.

## Input contract

Supply a UTF-8 CSV with one row per `(customer_id, snapshot_date)` and these columns:

| Column | Meaning |
| --- | --- |
| `customer_id` | Stable visitor identifier; the same visitor may have multiple dated snapshots within one split. |
| `snapshot_date` | Prediction date T (`YYYY-MM-DD`). |
| `feature_end` | Latest timestamp used by any supplied feature, reduced to an ISO date; must be at or before T. The data owner must still audit every source feature. |
| `label_end` | End of the future confirmation horizon; must be after T and no later than `--observed-through`. |
| `label_status` | `active` or `ghost` for supervised rows. `unknown`, `candidate`, `inactive`, and `recovered` are excluded and need a blank `target_ghost`. The final mapping requires D-03 approval. |
| `target_ghost` | `0` for active, `1` for ghost, blank for excluded rows. |
| `split` | `train`, `validation`, or `test`, assigned by Kiệt's approved visitor-aware temporal split. |
| Selected feature columns | Explicit numeric pre-T feature names, such as `sessions_4w` and `recency_days`. Blank values are imputed from train only. |

The script rejects duplicate visitor/date pairs, visitors crossing splits, overlapping label horizons between splits, unobservable labels, post-T feature dates, and feature names that identify targets or future fields. These checks do not prove the scientific validity of the input; Lâm and Kiệt must review cohort, labels, per-feature provenance, and the split manifest.

## Run

From the repository root, install only the benchmark dependencies and run:

```bash
python -m pip install -r research/baselines/requirements-decision-tree.txt
python research/baselines/decision_tree.py --input data/processed/modeling_snapshots.csv --output data/processed/decision_tree/results.json --features sessions_4w recency_days --observed-through 2015-09-14 --label-version D-03-approved-v1 --split-version D-05-approved-v1
python -m pytest research/baselines/tests -q
```

Dates and versions above are example arguments, not approved study decisions. The output stays in the ignored `data/processed/` directory. Record the CSV hash, generation command, cohort counts, label definition, and reviewer in `docs/evidence_register.md` before copying any result into the report. For shared review, publish only a small, approved result summary without raw visitor records.

The algorithm selects maximum depth and minimum leaf size by validation PR-AUC. It reports untouched test PR-AUC, ROC-AUC, precision, recall, F1, Brier score, class support, confusion matrix, and impurity-based feature importance at a fixed 0.5 threshold. Tree probabilities may be poorly calibrated. Feature importance and splits are predictive associations, not causal effects. Compare its test result only with models using the same cohort, label, and split.
