"""Inference runtime loaded by the backend for POST /api/predict (AI-12).

Contract (docs/integration_handoff.md):
    predict(payload: dict) -> dict  with keys
        score (0..1), risk_label (low|medium|high), top_factors [{feature, contribution}],
        model_version, dataset_notice
    payload is exactly one of
        {"customer_id": "...", "snapshot_date": "YYYY-MM-DD"}   -> features looked up
        {"features": {<allowlisted pre-T feature>: number|null, ...}}
    LookupError  -> unknown customer/snapshot           (API 404)
    ValueError   -> invalid payload / features           (API 422)
    RuntimeError -> model or feature table unavailable   (API 503)

The ID path never derives anything itself: it reads the row Lâm's pipeline
built from events strictly before T (feature_max_event_time_utc < T is
re-checked here). Confirmation-window fields and labels are never read.

Environment overrides: GHOST_MODEL_PATH, GHOST_FEATURES_PATH.
"""
from __future__ import annotations

import math
import os
from datetime import date
from functools import lru_cache
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from .attribution import METHOD, local_contributions

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MODEL = ROOT / "ai" / "models" / "ghost_model.joblib"
DEFAULT_FEATURES = ROOT / "data" / "processed" / "customer_features.parquet"
TOP_K = 5


def _model_path() -> Path:
    return Path(os.environ.get("GHOST_MODEL_PATH", DEFAULT_MODEL))


def _features_path() -> Path:
    return Path(os.environ.get("GHOST_FEATURES_PATH", DEFAULT_FEATURES))


@lru_cache(maxsize=1)
def load_artifact() -> dict:
    path = _model_path()
    if not path.exists():
        raise RuntimeError(f"Model artifact not found: {path.name}")
    art = joblib.load(path)
    required = {"model", "features", "model_version", "threshold", "baseline", "dataset_notice"}
    missing = required - set(art)
    if missing:
        raise RuntimeError(f"Model artifact is incomplete: {sorted(missing)}")
    return art


@lru_cache(maxsize=1)
def _feature_table() -> pd.DataFrame:
    path = _features_path()
    if not path.exists():
        raise RuntimeError("Processed feature table is unavailable")
    table = pd.read_parquet(path) if path.suffix == ".parquet" else pd.read_csv(path)
    table["customer_id"] = (table["customer_id"] if "customer_id" in table else table["visitorid"]).astype(str)
    table["_snapshot"] = pd.to_datetime(table["snapshot_date"], utc=True).dt.strftime("%Y-%m-%d")
    return table


def reload() -> None:
    """Clear caches after replacing the model or feature table."""
    load_artifact.cache_clear()
    _feature_table.cache_clear()


# --------------------------------------------------------------------------- input handling
def _coerce(name: str, value) -> float:
    if value is None:
        return np.nan
    if isinstance(value, bool):
        return float(value)
    if not isinstance(value, (int, float)):
        raise ValueError(f"Feature {name} must be a number, boolean or null")
    value = float(value)
    if math.isnan(value) or math.isinf(value):
        raise ValueError(f"Feature {name} must be finite or null")
    return value


def _row_from_features(features: dict, allow: list[str]) -> pd.DataFrame:
    if not isinstance(features, dict) or not features:
        raise ValueError("features must be a non-empty object")
    unknown = sorted(set(features) - set(allow))
    if unknown:
        raise ValueError(f"Features not in the model allowlist: {unknown}")
    missing = [f for f in allow if f not in features]
    if missing:
        raise ValueError(f"Missing model features (send null when undefined): {missing}")
    row = {f: _coerce(f, features[f]) for f in allow}
    for f, v in row.items():
        if not np.isnan(v) and v < 0 and "slope" not in f:
            raise ValueError(f"Feature {f} must be >= 0")
    if all(np.isnan(v) for v in row.values()):
        raise ValueError("All features are null; not enough data to score")
    return pd.DataFrame([row], columns=allow)


def _row_from_id(customer_id: str, snapshot_date: str, art: dict) -> pd.DataFrame:
    try:
        parsed = date.fromisoformat(snapshot_date)
    except (TypeError, ValueError):
        raise ValueError("snapshot_date must be YYYY-MM-DD") from None
    if parsed.isoformat() != snapshot_date:
        raise ValueError("snapshot_date must be YYYY-MM-DD")
    table = _feature_table()
    match = table[(table["customer_id"] == str(customer_id)) & (table["_snapshot"] == snapshot_date)]
    scenario = art.get("scenario_id")
    if scenario and "scenario_id" in match:
        match = match[match["scenario_id"].astype(str) == str(scenario)]
    if match.empty:
        raise LookupError(f"No pre-T feature row for customer {customer_id} at {snapshot_date}")
    if len(match) > 1:
        raise ValueError("Ambiguous feature rows for this customer and snapshot")
    if "feature_max_event_time_utc" in match:
        max_t = pd.to_datetime(match["feature_max_event_time_utc"], utc=True).iloc[0]
        if pd.notna(max_t) and max_t >= pd.Timestamp(snapshot_date, tz="UTC"):
            raise ValueError("Feature row uses events at or after the snapshot; refusing to score")
    missing = [f for f in art["features"] if f not in match]
    if missing:
        raise RuntimeError(f"Feature table lacks model features: {missing}")
    from ..training.data import to_matrix
    return to_matrix(match.reset_index(drop=True), art["features"])


# --------------------------------------------------------------------------- public API
def predict(payload: dict) -> dict:
    if not isinstance(payload, dict):
        raise ValueError("payload must be an object")
    art = load_artifact()
    has_id = bool(payload.get("customer_id")) or bool(payload.get("snapshot_date"))
    has_features = payload.get("features") is not None
    if has_id == has_features:
        raise ValueError("Provide exactly one of customer_id + snapshot_date, or features")
    if has_features:
        X = _row_from_features(payload["features"], art["features"])
    else:
        if not (payload.get("customer_id") and payload.get("snapshot_date")):
            raise ValueError("customer_id and snapshot_date are both required")
        X = _row_from_id(str(payload["customer_id"]), str(payload["snapshot_date"]), art)

    model = art["model"]
    score = float(np.clip(model.predict_proba(X)[0, 1], 0.0, 1.0))
    bands = art["threshold"]["bands"]
    label = "high" if score >= bands["high"] else "medium" if score >= bands["medium"] else "low"
    factors = local_contributions(model, X, art["baseline"], top_k=TOP_K)[0]
    notice = (f"{art['dataset_notice']} Operating threshold {art['threshold']['operating_threshold']:.2f} "
              f"(validation). top_factors: {METHOD}, probability points, association only.")
    return {
        "score": round(score, 4),
        "risk_label": label,
        "top_factors": [{"feature": f["feature"], "contribution": f["contribution"]} for f in factors],
        "model_version": art["model_version"],
        "dataset_notice": notice,
    }


def model_info() -> dict:
    art = load_artifact()
    return {k: art.get(k) for k in ("model_version", "features", "threshold", "label_task", "label_version",
                                    "scenario_id", "split_version", "attribution_method", "created_utc")}
