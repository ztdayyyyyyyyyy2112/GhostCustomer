import csv
from pathlib import Path

import pytest

from research.baselines.decision_tree import run


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
        for index in range(6):
            ghost = index % 2 == 1
            result.append({
                "customer_id": f"{split}-{index}",
                "snapshot_date": snapshot,
                "feature_end": snapshot,
                "label_end": label_end,
                "label_status": "ghost" if ghost else "active",
                "target_ghost": "1" if ghost else "0",
                "split": split,
                "sessions_4w": "1" if ghost else "9",
                "recency_days": "8" if ghost else "1",
            })
    return result


def write_csv(path: Path, data):
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(data)


def execute(tmp_path, data, features=None):
    source = tmp_path / "snapshots.csv"
    output = tmp_path / "results.json"
    write_csv(source, data)
    return run(
        source, output, features or ["sessions_4w", "recency_days"],
        "2026-02-28", "label-v1", "split-v1",
    )


def test_runs_on_disjoint_temporal_splits_and_records_provenance(tmp_path):
    data = rows()
    data.append({
        **data[0], "customer_id": "unknown-1", "label_status": "unknown",
        "target_ghost": "", "label_end": "",
    })
    result = execute(tmp_path, data)
    assert result["test"]["n"] == 6
    assert result["test"]["ghost_n"] == 3
    assert result["excluded_status_counts"] == {"unknown": 1}
    assert result["test"]["pr_auc"] > result["majority_test"]["pr_auc"]
    assert result["input_sha256"] and result["label_version"] == "label-v1"
    assert (tmp_path / "results.json").is_file()


@pytest.mark.parametrize(
    ("change", "message"),
    [
        (lambda data: data[6].update(customer_id=data[0]["customer_id"]), "both train and validation"),
        (lambda data: data[0].update(feature_end="2026-01-02"), "after snapshot_date"),
        (lambda data: data[0].update(label_end="2026-01-15"), "overlap"),
        (lambda data: data[0].update(label_end="2026-03-01"), "not fully observable"),
        (lambda data: data[0].update(target_ghost="1"), "conflicts"),
    ],
)
def test_rejects_leakage_and_invalid_labels(tmp_path, change, message):
    data = rows()
    change(data)
    with pytest.raises(ValueError, match=message):
        execute(tmp_path, data)


def test_rejects_target_as_feature(tmp_path):
    with pytest.raises(ValueError, match="future-label field"):
        execute(tmp_path, rows(), ["target_ghost"])
