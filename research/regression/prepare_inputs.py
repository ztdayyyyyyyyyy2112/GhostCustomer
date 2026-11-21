"""Create ignored, provenance-checked regression inputs from the shared pipeline."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def run(features_path: Path, labels_path: Path, out: Path) -> dict:
    features = pd.read_parquet(features_path)
    labels = pd.read_parquet(labels_path)
    fcols = ["visitorid", "snapshot_date", "feature_max_event_time_utc", "feature_sessions_4w",
             "feature_views_4w", "feature_recency_days", "feature_baseline_sessions_per_week",
             "feature_observation_sessions_per_week"]
    lcols = ["visitorid", "snapshot_date", "label_end_utc", "horizon_mature", "label_status",
             "target_ghost", "future_sessions"]
    if not set(fcols) <= set(features) or not set(lcols) <= set(labels):
        raise ValueError("Shared feature/label schema mismatch")
    merged = features[fcols].merge(labels[lcols], on=["visitorid", "snapshot_date"], validate="one_to_one")
    if merged.duplicated(["visitorid", "snapshot_date"]).any():
        raise ValueError("Duplicate visitor snapshots")
    if not (merged.feature_max_event_time_utc < merged.snapshot_date).all():
        raise ValueError("Feature timeline crosses the snapshot boundary")
    out.mkdir(parents=True, exist_ok=True)
    base = pd.DataFrame({
        "visitorid": merged.visitorid.astype(str),
        "snapshot_date": pd.to_datetime(merged.snapshot_date, utc=True).dt.strftime("%Y-%m-%d"),
        "feature_max_event_time": pd.to_datetime(merged.feature_max_event_time_utc, utc=True).dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "outcome_end": pd.to_datetime(merged.label_end_utc, utc=True).dt.strftime("%Y-%m-%d"),
        "label_end": pd.to_datetime(merged.label_end_utc, utc=True).dt.strftime("%Y-%m-%d"),
        "label_status": merged.label_status,
        "target_ghost": merged.target_ghost,
        "sessions": merged.feature_sessions_4w,
        "recency_days": merged.feature_recency_days,
        "engagement_change": merged.feature_observation_sessions_per_week - merged.feature_baseline_sessions_per_week,
        "feature_sessions_4w": merged.feature_sessions_4w,
        "feature_views_4w": merged.feature_views_4w,
        "feature_recency_days": merged.feature_recency_days,
        "next_engagement": merged.future_sessions / 2.0,
    })
    # No immature outcome is exported to the OLS table. Logit accepts unknowns with null targets
    # and explicitly excludes them inside its own provenance and split checks.
    ols = base.loc[merged.horizon_mature].copy()
    ols["outcome_end"] = base.loc[merged.horizon_mature, "outcome_end"]
    logit = base.drop(columns=["outcome_end", "next_engagement", "feature_sessions_4w",
                               "feature_views_4w", "feature_recency_days"])
    ols = ols.drop(columns=["label_end", "label_status", "target_ghost", "sessions",
                            "recency_days", "engagement_change"])
    ols_path = out / "ols_input.csv"
    logit_path = out / "logit_input.csv"
    ols.to_csv(ols_path, index=False)
    logit.to_csv(logit_path, index=False)
    manifest = {
        "data_mode": "real", "features_sha256": sha(features_path), "labels_sha256": sha(labels_path),
        "ols_rows": len(ols), "logit_rows": len(logit),
        "ols_input_sha256": sha(ols_path), "logit_input_sha256": sha(logit_path),
        "outcome_definition": "Observed number of future sessions in [T,T+2 weeks), divided by 2 to get sessions/week; only mature horizons enter OLS",
        "predictor_policy": "All predictors are measured before T. Future outcomes are excluded from X.",
        "decision_status": "Proposed 4+2+2 cohort and label; exploratory evidence only",
    }
    (out / "input_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--features", type=Path, default=ROOT / "data/processed/customer_features.parquet")
    p.add_argument("--labels", type=Path, default=ROOT / "data/processed/customer_labels.parquet")
    p.add_argument("--out", type=Path, default=ROOT / "data/processed/regression")
    a = p.parse_args()
    print(json.dumps(run(a.features, a.labels, a.out), indent=2))
