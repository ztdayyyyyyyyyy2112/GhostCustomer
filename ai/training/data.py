"""Load Lâm's processed tables and build the supervised modeling frame (AI-01/AI-03).

Feature rows come from customer_features.parquet (pre-T only, half-open
[window_start, T)); labels from customer_labels.parquet (confirmation [T, T+C)).
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

from . import config

FORBIDDEN = re.compile(
    r"(^|_)(id|visitorid|target|label|future|confirmation|post|status|split|snapshot|date|time|utc)(_|$)",
    re.IGNORECASE,
)


# --------------------------------------------------------------------------- IO
def read_table(path: str | Path) -> pd.DataFrame:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"{path} not found. Run Lâm's data pipeline first (data/README.md).")
    if path.suffix == ".parquet":
        return pd.read_parquet(path)
    if path.suffix == ".csv":
        return pd.read_csv(path)
    raise ValueError(f"Unsupported table format: {path.suffix}")


def _utc(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series, utc=True)


def load_observed_through() -> pd.Timestamp:
    cfg = json.loads(config.PIPELINE_CONFIG.read_text(encoding="utf-8"))
    return pd.Timestamp(cfg["time"]["observed_through"]).tz_convert("UTC")


def merge_features_labels(features: pd.DataFrame, labels: pd.DataFrame) -> pd.DataFrame:
    f = features.copy()
    lab = labels.copy()
    for frame in (f, lab):
        frame["snapshot_date"] = _utc(frame["snapshot_date"])
    keep = [c for c in ["visitorid", "snapshot_date", "label_end_utc", "label_status", "target_ghost",
                        "horizon_mature", "label_version", "params_hash"] if c in lab.columns]
    merged = f.merge(lab[keep], on=["visitorid", "snapshot_date"], how="inner", validate="one_to_one")
    merged["label_end_utc"] = _utc(merged["label_end_utc"])
    if "customer_id" not in merged:
        merged["customer_id"] = merged["visitorid"].astype(str)
    merged["customer_id"] = merged["customer_id"].astype(str)
    return merged.sort_values(["snapshot_date", "visitorid"], kind="mergesort").reset_index(drop=True)


def load_processed(features_path=None, labels_path=None) -> pd.DataFrame:
    return merge_features_labels(read_table(features_path or config.FEATURES_PATH),
                                 read_table(labels_path or config.LABELS_PATH))


# --------------------------------------------------------------------------- features
def all_feature_columns(df: pd.DataFrame) -> list[str]:
    return [c for c in df.columns if c.startswith("feature_") and c not in config.NON_FEATURE_COLUMNS]


def feature_set(df: pd.DataFrame, name: str = config.PRIMARY_FEATURE_SET) -> list[str]:
    cols = all_feature_columns(df)
    if name == "full":
        chosen = cols
    elif name == "no_target_components":
        chosen = [c for c in cols if c not in config.TARGET_COMPONENT_FEATURES]
    elif name == "observation_only":
        chosen = [c for c in config.OBSERVATION_ONLY_FEATURES if c in cols]
    elif name == "baseline_only":
        chosen = [c for c in ["feature_baseline_sessions_per_week"] if c in cols]
    else:
        raise ValueError(f"Unknown feature set {name!r}; choose from {config.FEATURE_SETS}")
    check_no_forbidden(chosen)
    if not chosen:
        raise ValueError(f"Feature set {name!r} is empty for this table")
    return chosen


def check_no_forbidden(features: list[str]) -> None:
    """IDs, dates, labels, splits and future fields can never be model inputs."""
    bad = [f for f in features
           if f in config.NON_FEATURE_COLUMNS or FORBIDDEN.search(f.removeprefix("feature_"))]
    if bad:
        raise ValueError(f"Forbidden model inputs: {bad}")
    if len(set(features)) != len(features):
        raise ValueError("Duplicate feature names")


def to_matrix(df: pd.DataFrame, features: list[str]) -> pd.DataFrame:
    """Float matrix: booleans -> 0/1, non-numeric -> error, +-inf -> NaN."""
    out = pd.DataFrame(index=df.index)
    for col in features:
        s = df[col]
        if s.dtype == bool or str(s.dtype) == "boolean":
            s = s.astype("Float64")
        elif s.dtype == object:
            s = s.map({True: 1.0, False: 0.0, "True": 1.0, "False": 0.0, "true": 1.0, "false": 0.0}).where(
                s.isin([True, False, "True", "False", "true", "false"]), pd.to_numeric(s, errors="raise"))
        out[col] = pd.to_numeric(s, errors="raise").astype("float64")
    return out.replace([np.inf, -np.inf], np.nan)


# --------------------------------------------------------------------------- supervised frame
def leakage_audit(df: pd.DataFrame, observed_through: pd.Timestamp) -> dict:
    """Row-level checks that features are pre-T and labels are fully observed."""
    checks = {}
    if "feature_max_event_time_utc" in df:
        max_t = _utc(df["feature_max_event_time_utc"])
        checks["features_before_snapshot"] = bool((max_t.isna() | (max_t < df["snapshot_date"])).all())
    checks["label_after_snapshot"] = bool((df["label_end_utc"] > df["snapshot_date"]).all())
    checks["label_observed"] = bool((df["label_end_utc"] <= observed_through).all())
    checks["unique_visitor_snapshot"] = not df.duplicated(["visitorid", "snapshot_date"]).any()
    return checks


def build_supervised(merged: pd.DataFrame, task: str = config.DEFAULT_LABEL_TASK,
                     observed_through: pd.Timestamp | None = None) -> pd.DataFrame:
    """Mature rows of the chosen label task with integer column `y`."""
    if task not in config.LABEL_TASKS:
        raise ValueError(f"Unknown label task {task!r}")
    spec = config.LABEL_TASKS[task]
    observed_through = observed_through or load_observed_through()
    status = merged["label_status"].astype(str).str.lower()
    mature = merged.get("horizon_mature", pd.Series(True, index=merged.index)).astype(bool)
    mature &= merged["label_end_utc"] <= observed_through
    keep = mature & status.isin(spec["positive"] + spec["negative"])
    data = merged.loc[keep].copy()
    data["label_status"] = status[keep]
    data["y"] = data["label_status"].isin(spec["positive"]).astype(int)
    audit = leakage_audit(data, observed_through)
    failed = [k for k, ok in audit.items() if not ok]
    if failed:
        raise ValueError(f"Leakage audit failed: {failed}")
    if data["y"].nunique() < 2:
        raise ValueError("Supervised frame needs both classes")
    return data.reset_index(drop=True)


def is_synthetic(df: pd.DataFrame) -> bool:
    return "is_synthetic" in df and bool(pd.Series(df["is_synthetic"]).astype(bool).any())
