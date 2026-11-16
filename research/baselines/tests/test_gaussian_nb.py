import csv
from pathlib import Path

import pytest

from research.baselines.gaussian_nb import run


FIELDS = [
    "customer_id", "snapshot_date", "feature_end", "label_end",
    "label_status", "target_ghost", "split", "sessions_4w", "recency_days",
]


def rows():
    result = []
    for split, snapshot, label_end in (
        ("train", "2026-01-01", "2026-01-08"),
        ("validation", "2026-01-15", "2026-01-22"),
        ("test", "2026-02-01", "2026-02-08"),
    ):
        for index in range(8):
            ghost = index % 2 == 1
            result.append({
                "customer_id": f"{split}-{index}",
                "snapshot_date": snapshot,
                "feature_end": snapshot,
                "label_end": label_end,
                "label_status": "ghost" if ghost else "active",
                "target_ghost": "1" if ghost else "0",
                "split": split,
                "sessions_4w": "" if index == 0 else ("1" if ghost else "9"),
                "recency_days": "8" if ghost else "1",
            })
    return result


def write_csv(path: Path, data):
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(data)


def execute(tmp_path, data):
    source = tmp_path / "snapshots.csv"
    output = tmp_path / "results.json"
    write_csv(source, data)
    result = run(
        source, output, ["sessions_4w", "recency_days"],
        "2026-02-28", "label-v1", "split-v1",
    )
    return result, output


def test_scores_approved_split_contract_and_writes_metrics(tmp_path):
    result, output = execute(tmp_path, rows())

    assert result["algorithm"] == "GaussianNB"
    assert result["owner"] == "Cao Phan Lam"
    assert result["selected_on"] == "validation PR-AUC"
    assert result["test"]["n"] == 8
    assert result["test"]["ghost_n"] == 4
    assert result["test"]["pr_auc"] > result["majority_test"]["pr_auc"]
    assert result["hyperparameters"]["var_smoothing"] in result["smoothing_candidates"]
    assert result["input_sha256"] and output.is_file()


def test_rejects_feature_missing_for_all_training_rows(tmp_path):
    data = rows()
    for row in data:
        if row["split"] == "train":
            row["sessions_4w"] = ""

    with pytest.raises(ValueError, match="entirely missing in training data"):
        execute(tmp_path, data)
