"""Reproducible, snapshot-safe Gaussian Naive Bayes benchmark for future Ghost labels."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from sklearn.impute import SimpleImputer
from sklearn.metrics import average_precision_score
from sklearn.naive_bayes import GaussianNB
from sklearn.pipeline import make_pipeline

from research.baselines.decision_tree import iso_date, metrics, read_input, validate_splits


SMOOTHING_CANDIDATES = (1e-12, 1e-10, 1e-9, 1e-7, 1e-5)


def run(
    input_path: Path,
    output_path: Path,
    features: list[str],
    observed_through: str,
    label_version: str,
    split_version: str,
) -> dict:
    if not label_version.strip() or not split_version.strip():
        raise ValueError("label_version and split_version are required")
    cutoff = iso_date(observed_through, "observed_through", 0)
    records, excluded = read_input(input_path, features, cutoff)
    groups = validate_splits(records)
    arrays = {
        split: (
            np.array([row[5] for row in rows], dtype=float),
            np.array([row[4] for row in rows], dtype=int),
        )
        for split, rows in groups.items()
    }
    if np.isnan(arrays["train"][0]).all(axis=0).any():
        raise ValueError("A feature is entirely missing in training data")

    x_train, y_train = arrays["train"]
    x_val, y_val = arrays["validation"]
    candidates = []
    for smoothing in SMOOTHING_CANDIDATES:
        model = make_pipeline(
            SimpleImputer(strategy="median"),
            GaussianNB(var_smoothing=smoothing),
        )
        model.fit(x_train, y_train)
        val_scores = model.predict_proba(x_val)[:, 1]
        candidates.append((float(average_precision_score(y_val, val_scores)), smoothing, model))
    # Choose smoothing on validation PR-AUC; ties retain the first (least-smoothed) candidate.
    _, smoothing, model = max(candidates, key=lambda item: item[0])

    val_scores = model.predict_proba(x_val)[:, 1]
    x_test, y_test = arrays["test"]
    test_scores = model.predict_proba(x_test)[:, 1]
    majority = int(y_train.mean() >= 0.5)
    majority_scores = np.full(len(y_test), majority, dtype=float)
    result = {
        "algorithm": "GaussianNB",
        "owner": "Cao Phan Lam",
        "input_sha256": hashlib.sha256(input_path.read_bytes()).hexdigest(),
        "label_version": label_version,
        "split_version": split_version,
        "observed_through": cutoff.isoformat(),
        "feature_names": features,
        "excluded_status_counts": excluded,
        "selected_on": "validation PR-AUC",
        "smoothing_candidates": list(SMOOTHING_CANDIDATES),
        "hyperparameters": {"var_smoothing": smoothing},
        "decision_threshold": 0.5,
        "train": {"n": int(len(y_train)), "ghost_n": int(y_train.sum())},
        "validation": metrics(y_val, val_scores),
        "test": metrics(y_test, test_scores),
        "majority_test": metrics(y_test, majority_scores),
        "assumption": "Features are conditionally independent and Gaussian within each class.",
        "notice": (
            "Research benchmark only. Gaussian and conditional-independence assumptions may fit "
            "skewed event counts poorly; interpret only with an approved real-data cohort, label, "
            "feature allowlist, and shared temporal split."
        ),
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--features", required=True, nargs="+")
    parser.add_argument("--observed-through", required=True)
    parser.add_argument("--label-version", required=True)
    parser.add_argument("--split-version", required=True)
    args = parser.parse_args()
    try:
        result = run(
            args.input, args.output, args.features, args.observed_through,
            args.label_version, args.split_version,
        )
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    print(f"Wrote {args.output} (test PR-AUC: {result['test']['pr_auc']:.4f})")


if __name__ == "__main__":
    main()
