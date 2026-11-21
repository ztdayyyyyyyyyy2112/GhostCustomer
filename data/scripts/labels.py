from __future__ import annotations

import hashlib
import json

import pandas as pd

from data.scripts.features import _scenario


LABEL_COLUMNS = [
    "visitorid", "snapshot_date", "label_end_utc", "label_status", "target_ghost", "target_disengaged",
    "future_activity", "future_events", "future_sessions", "future_purchases", "future_engagement_rate",
    "horizon_mature", "unknown_reason", "observation_declined", "display_status", "label_rule_id", "label_version", "params_hash",
]


def _utc(value) -> pd.Timestamp:
    timestamp = pd.Timestamp(value)
    return timestamp.tz_localize("UTC") if timestamp.tzinfo is None else timestamp.tz_convert("UTC")


def build_labels(
    events: pd.DataFrame,
    sessions: pd.DataFrame,
    cohort: pd.DataFrame,
    features: pd.DataFrame,
    config: dict,
    theta: float | None = None,
    require_no_purchase: bool | None = None,
    engagement_unit: str | None = None,
) -> pd.DataFrame:
    if cohort.empty:
        return pd.DataFrame(columns=LABEL_COLUMNS)
    theta = float(config["labels"]["preferred_theta"] if theta is None else theta)
    require_no_purchase = bool(config["labels"]["preferred_require_no_purchase"] if require_no_purchase is None else require_no_purchase)
    engagement_unit = engagement_unit or config["labels"]["preferred_engagement_unit"]
    if theta not in config["labels"]["theta"] or engagement_unit not in config["labels"]["engagement_unit"]:
        raise ValueError("label parameters are not present in the shared config")
    candidates = cohort.loc[cohort.history_eligible].copy() if "history_eligible" in cohort else cohort.copy()
    candidates = candidates.merge(
        features[["visitorid", "snapshot_date", "scenario_id", "feature_baseline_sessions_per_week", "feature_observation_sessions_per_week", "feature_baseline_events_per_week", "feature_observation_events_per_week"]],
        on=["visitorid", "snapshot_date", "scenario_id"], how="left", validate="one_to_one",
    )
    rows = []
    observed_through = _utc(config["time"]["observed_through"])
    for (scenario_id, snapshot), group in candidates.groupby(["scenario_id", "snapshot_date"], sort=True):
        scenario = _scenario(config, scenario_id)
        t = _utc(snapshot)
        end = t + pd.Timedelta(7 * int(scenario["confirmation_weeks"]), unit="d")
        confirmation_weeks = int(scenario["confirmation_weeks"])
        mature = end <= observed_through
        future_events = events.loc[(events.event_time_utc >= t) & (events.event_time_utc < end)]
        future_sessions = sessions.loc[(sessions.session_start_utc >= t) & (sessions.session_start_utc < end)]
        event_counts = future_events.groupby("visitorid", sort=False).agg(
            future_events=("event_time_utc", "size"),
            future_purchases=("event_type", lambda values: int(values.eq("transaction").sum())),
        ).reset_index()
        session_counts = future_sessions.groupby("visitorid", sort=False).size().rename("future_sessions").reset_index()
        labeled = group.merge(event_counts, on="visitorid", how="left").merge(session_counts, on="visitorid", how="left")
        for column in ("future_events", "future_purchases", "future_sessions"):
            labeled[column] = labeled[column].fillna(0).astype("int64")
        metric_count = labeled.future_sessions if engagement_unit == "sessions" else labeled.future_events
        labeled["future_engagement_rate"] = metric_count / confirmation_weeks
        baseline_rate = labeled[f"feature_baseline_{engagement_unit}_per_week"]
        observation_rate = labeled[f"feature_observation_{engagement_unit}_per_week"]
        conf_ratio = (labeled.future_engagement_rate / baseline_rate).where(baseline_rate.gt(0))
        obs_ratio = (observation_rate / baseline_rate).where(baseline_rate.gt(0))
        observation_declined = obs_ratio.lt(theta)
        unscorable = baseline_rate.isna() | baseline_rate.le(0)
        inactive = labeled.future_events.eq(0)
        recovered = observation_declined & conf_ratio.ge(theta)
        ghost = labeled.future_events.gt(0) & conf_ratio.lt(theta)
        if require_no_purchase:
            ghost &= labeled.future_purchases.eq(0)
        status = pd.Series("active", index=labeled.index, dtype="string")
        status.loc[ghost] = "ghost"
        status.loc[recovered & ~inactive] = "recovered"
        status.loc[inactive] = "inactive"
        status.loc[unscorable & ~inactive] = "unknown"
        if not mature:
            status[:] = "unknown"
        labeled["label_status"] = status
        labeled["target_ghost"] = pd.array(status.map({"ghost": 1, "active": 0, "recovered": 0, "inactive": 0}), dtype="Int8")
        labeled["target_disengaged"] = pd.array(status.map({"ghost": 1, "active": 0, "recovered": 0, "inactive": 1}), dtype="Int8")
        labeled["unknown_reason"] = pd.Series(pd.NA, index=labeled.index, dtype="string")
        labeled.loc[unscorable, "unknown_reason"] = "zero_baseline_sessions"
        if not mature:
            labeled["unknown_reason"] = "immature_horizon"
        labeled["observation_declined"] = observation_declined.astype("boolean")
        labeled.loc[unscorable, "observation_declined"] = pd.NA
        labeled["display_status"] = labeled.label_status
        candidate = labeled.label_status.eq("unknown") & labeled.observation_declined.eq(True)
        labeled.loc[candidate, "display_status"] = "candidate"
        labeled["label_end_utc"] = end
        labeled["horizon_mature"] = mature
        theta_id = str(theta).replace(".", "p")
        no_purchase_id = "no_purchase" if require_no_purchase else "allow_purchase"
        labeled["label_rule_id"] = f"{engagement_unit}_vs_baseline_theta_{theta_id}_{no_purchase_id}"
        labeled["label_version"] = config["labels"]["version"]
        params = {
            "config_version": config["config_version"], "scenario": scenario,
            "theta": theta, "engagement_unit": engagement_unit,
            "require_no_purchase": require_no_purchase,
            "session_gap_minutes": config["sessions"]["preferred_gap_minutes"],
            "duplicate_policy": config["duplicate_policy"],
        }
        params_hash = hashlib.sha256(json.dumps(params, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        labeled["params_hash"] = params_hash
        labeled["future_activity"] = metric_count.astype("int64")
        rows.append(labeled.reindex(columns=LABEL_COLUMNS))

    result = pd.concat(rows, ignore_index=True).sort_values(["visitorid", "snapshot_date"], kind="mergesort").reset_index(drop=True)
    censored = ~result.horizon_mature
    if not (result.loc[censored, "label_status"].eq("unknown").all() and result.loc[censored, "unknown_reason"].eq("immature_horizon").all()):
        raise AssertionError("censored confirmation rows must be unknown")
    return result


def minimal_labels(labels: pd.DataFrame) -> pd.DataFrame:
    result = labels[["visitorid", "snapshot_date", "label_end_utc", "label_status", "target_ghost"]].copy()
    result["snapshot_date"] = pd.to_datetime(result.snapshot_date, utc=True).dt.strftime("%Y-%m-%d")
    result["label_end"] = pd.to_datetime(result.label_end_utc, utc=True).dt.strftime("%Y-%m-%d")
    return result[["visitorid", "snapshot_date", "label_end", "label_status", "target_ghost"]]
