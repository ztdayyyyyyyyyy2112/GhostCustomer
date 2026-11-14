"""Reproducible, snapshot-safe Decision Tree benchmark for future Ghost labels."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
from collections import Counter
from datetime import date
from pathlib import Path

import numpy as np
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.pipeline import make_pipeline
from sklearn.tree import DecisionTreeClassifier


REQUIRED = {
    "customer_id", "snapshot_date", "feature_end", "label_end",
    "label_status", "target_ghost", "split",
}
SPLITS = ("train", "validation", "test")
EXCLUDED_STATUSES = {"unknown", "candidate", "inactive", "recovered"}
FORBIDDEN_FEATURE = re.compile(
    r"(^|_)(id|target|label|future|confirmation|post|status|split|snapshot|date|time)(_|$)",
    re.IGNORECASE,
)


def iso_date(value: str, field: str, line: int) -> date:
    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"line {line}: {field} must be YYYY-MM-DD") from exc
    if parsed.isoformat() != value:
        raise ValueError(f"line {line}: {field} must be YYYY-MM-DD")
    return parsed


def read_input(path: Path, features: list[str], observed_through: date):
    if not features or len(features) != len(set(features)):
        raise ValueError("Provide distinct, explicit pre-T feature names")
    if any(FORBIDDEN_FEATURE.search(name) for name in features):
        raise ValueError("Feature list contains an ID, date, split, status, or future-label field")

    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        fields = set(reader.fieldnames or [])
        absent = (REQUIRED | set(features)) - fields
        if absent:
            raise ValueError(f"Missing CSV columns: {', '.join(sorted(absent))}")
        records = []
        excluded = Counter()
        seen = set()
        for line, row in enumerate(reader, start=2):
            if None in row:
                raise ValueError(f"line {line}: extra CSV fields")
            customer_id = (row["customer_id"] or "").strip()
            if not customer_id:
                raise ValueError(f"line {line}: empty customer_id")
            snapshot = iso_date(row["snapshot_date"], "snapshot_date", line)
            key = (customer_id, snapshot)
            if key in seen:
                raise ValueError(f"line {line}: duplicate customer_id and snapshot_date")
            seen.add(key)
            status = (row["label_status"] or "").strip().lower()
            if status in EXCLUDED_STATUSES:
                if (row["target_ghost"] or "").strip():
                    raise ValueError(f"line {line}: excluded status must have blank target_ghost")
                excluded[status] += 1
                continue
            if status not in {"active", "ghost"}:
                raise ValueError(f"line {line}: unsupported label_status {status!r}")
            target = (row["target_ghost"] or "").strip()
            if target != ("1" if status == "ghost" else "0"):
                raise ValueError(f"line {line}: target_ghost conflicts with label_status")
            feature_end = iso_date(row["feature_end"], "feature_end", line)
            label_end = iso_date(row["label_end"], "label_end", line)
            if feature_end > snapshot:
                raise ValueError(f"line {line}: feature_end occurs after snapshot_date")
            if not snapshot < label_end <= observed_through:
                raise ValueError(f"line {line}: label horizon is not fully observable after T")
            split = (row["split"] or "").strip().lower()
            if split not in SPLITS:
                raise ValueError(f"line {line}: split must be train, validation, or test")
            values = []
            for feature in features:
                raw = (row[feature] or "").strip()
                try:
                    value = float(raw) if raw else math.nan
                except ValueError as exc:
                    raise ValueError(f"line {line}: {feature} must be numeric or blank") from exc
                if math.isinf(value):
                    raise ValueError(f"line {line}: {feature} must be finite")
                values.append(value)
            records.append((customer_id, snapshot, label_end, split, int(target), values))
    return records, dict(excluded)


def validate_splits(records) -> dict[str, list]:
    groups = {split: [row for row in records if row[3] == split] for split in SPLITS}
    for split, rows in groups.items():
        if not rows or {row[4] for row in rows} != {0, 1}:
            raise ValueError(f"{split} must contain both active and ghost cases")
    ids = {split: {row[0] for row in rows} for split, rows in groups.items()}
    for first, second in (("train", "validation"), ("train", "test"), ("validation", "test")):
        if ids[first] & ids[second]:
            raise ValueError(f"customer_id appears in both {first} and {second}")
    for earlier, later in (("train", "validation"), ("validation", "test")):
        if max(row[2] for row in groups[earlier]) >= min(row[1] for row in groups[later]):
            raise ValueError(f"{earlier} labels overlap the {later} snapshot period")
    return groups


def metrics(y: np.ndarray, scores: np.ndarray) -> dict:
    labels = (scores >= 0.5).astype(int)
    tn, fp, fn, tp = confusion_matrix(y, labels, labels=[0, 1]).ravel()
    return {
        "n": int(len(y)),
        "ghost_n": int(y.sum()),
        "ghost_prevalence": float(y.mean()),
        "pr_auc": float(average_precision_score(y, scores)),
        "roc_auc": float(roc_auc_score(y, scores)),
        "precision": float(precision_score(y, labels, zero_division=0)),
        "recall": float(recall_score(y, labels, zero_division=0)),
        "f1": float(f1_score(y, labels, zero_division=0)),
        "brier": float(brier_score_loss(y, scores)),
        "confusion_matrix": [[int(tn), int(fp)], [int(fn), int(tp)]],
    }


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
    for depth in (2, 4, 6):
        for leaf in (1, 5, 20):
            model = make_pipeline(
                SimpleImputer(strategy="median"),
                DecisionTreeClassifier(
                    max_depth=depth, min_samples_leaf=leaf,
                    class_weight="balanced", random_state=42,
                ),
            )
            model.fit(x_train, y_train)
            score = model.predict_proba(x_val)[:, 1]
            candidates.append((float(average_precision_score(y_val, score)), depth, leaf, model))
    # PR-AUC selects on validation only; ties prefer shallower, larger-leaf trees.
    _, depth, leaf, model = max(candidates, key=lambda item: (item[0], -item[1], item[2]))
    tree = model.named_steps["decisiontreeclassifier"]
    val_scores = model.predict_proba(x_val)[:, 1]
    x_test, y_test = arrays["test"]
    test_scores = model.predict_proba(x_test)[:, 1]
    majority = int(y_train.mean() >= 0.5)
    majority_scores = np.full(len(y_test), majority, dtype=float)
    digest = hashlib.sha256(input_path.read_bytes()).hexdigest()
    result = {
        "algorithm": "DecisionTreeClassifier",
        "owner": "Ha Nguyen Viet Thanh",
        "input_sha256": digest,
        "label_version": label_version,
        "split_version": split_version,
        "observed_through": cutoff.isoformat(),
        "feature_names": features,
        "excluded_status_counts": excluded,
        "selected_on": "validation PR-AUC",
        "hyperparameters": {"max_depth": depth, "min_samples_leaf": leaf, "class_weight": "balanced", "random_state": 42},
        "decision_threshold": 0.5,
        "train": {"n": int(len(y_train)), "ghost_n": int(y_train.sum())},
        "validation": metrics(y_val, val_scores),
        "test": metrics(y_test, test_scores),
        "majority_test": metrics(y_test, majority_scores),
        "feature_importances": [
            {"feature": name, "importance": float(importance)}
            for name, importance in sorted(
                zip(features, tree.feature_importances_), key=lambda pair: -pair[1]
            )
        ],
        "notice": "Research benchmark; interpret only with an approved real-data cohort and label.",
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
