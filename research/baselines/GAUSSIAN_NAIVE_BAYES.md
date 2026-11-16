# Lâm's Gaussian Naive Bayes baseline

This is a research benchmark for RQ3, not the model served by `/api/predict`. It consumes the same modeling-snapshot CSV contract and split checks as `decision_tree.py`, so it can be compared with Thành's tree on the exact same visitor-aware temporal split and feature allowlist.

## Run

Install the existing baseline dependencies and run from the repository root:

```bash
python -m pip install -r research/baselines/requirements-decision-tree.txt
python -m research.baselines.gaussian_nb --input data/processed/modeling_snapshots.csv --output data/processed/gaussian_nb/results.json --features <approved-feature-names> --observed-through <YYYY-MM-DD> --label-version <approved-label-version> --split-version <approved-split-version>
python -m pytest research/baselines/tests -q
```

Do not substitute proposed dates, labels, features, or split IDs. The shared split manifest and feature allowlist are still pending Kiệt's approval; therefore, no real-data score is reported by this implementation. The generated result stays under ignored `data/processed/`.

## Method and limits

Median imputation is fitted on the training partition only. `var_smoothing` is selected from a fixed candidate grid by validation PR-AUC; the test partition is evaluated once after selection. The output uses the Decision Tree benchmark's PR-AUC, ROC-AUC, precision, recall, F1, Brier score, class support, confusion matrix, and 0.5 threshold, and includes an all-majority test comparator.

Gaussian Naive Bayes assumes features are conditionally independent and Gaussian within each class. Retail event counts are often skewed and discrete, so this is a deliberately simple comparator, not an expected winner. Brier score alone does not establish good calibration. The relative Ghost label may also overlap with baseline-period features; follow the approved feature allowlist and report the planned ablation before making predictive claims. A benchmark result is comparable only when its input hash, cohort, label version, feature list, and split version match the Decision Tree run.
