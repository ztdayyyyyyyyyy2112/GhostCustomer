from __future__ import annotations

import numpy as np
import pandas as pd

from data.scripts.config import FEATURE_COLUMNS


EVENT_TYPES = ("view", "addtocart", "transaction")
WINDOW_FEATURES = (1, 2, 4, 6)
WEEK = pd.Timedelta(7, unit="d")


def _events_in(events: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    return events.loc[(events.event_time_utc >= start) & (events.event_time_utc < end)]


def _event_counts(events: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    selected = _events_in(events, start, end)
    if selected.empty:
        return pd.DataFrame(columns=["visitorid", "views", "carts", "purchases", "events"])
    counts = selected.groupby(["visitorid", "event_type"], observed=True, sort=False).size().unstack(fill_value=0)
    counts = counts.reindex(columns=EVENT_TYPES, fill_value=0)
    counts.columns = ["views", "carts", "purchases"]
    counts["events"] = counts.sum(axis=1)
    return counts.reset_index()


def _session_counts(sessions: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp, suffix: str) -> pd.DataFrame:
    selected = sessions.loc[(sessions.session_start_utc >= start) & (sessions.session_start_utc < end)]
    if selected.empty:
        return pd.DataFrame(columns=["visitorid", f"sessions_{suffix}"])
    return selected.groupby("visitorid", sort=False).size().rename(f"sessions_{suffix}").reset_index()


def _merge_count(base: pd.DataFrame, counts: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    result = base.merge(counts, on="visitorid", how="left")
    for column in columns:
        result[column] = pd.to_numeric(result[column], errors="coerce").fillna(0).astype("int64")
    return result


def _scenario(config: dict, scenario_id: str) -> dict:
    for scenario in config["scenarios"]:
        if scenario["id"] == scenario_id:
            return scenario
    raise ValueError(f"unknown scenario_id: {scenario_id}")


def build_features(events: pd.DataFrame, sessions: pd.DataFrame, cohort: pd.DataFrame, config: dict) -> pd.DataFrame:
    if cohort.empty:
        return pd.DataFrame(columns=FEATURE_COLUMNS)
    eligible = cohort.loc[cohort.history_eligible].copy() if "history_eligible" in cohort else cohort.copy()
    frames: list[pd.DataFrame] = []
    for scenario_id, rows in eligible.groupby("scenario_id", sort=False):
        scenario = _scenario(config, scenario_id)
        b_weeks, o_weeks = scenario["baseline_weeks"], scenario["observation_weeks"]
        for snapshot, snapshot_rows in rows.groupby("snapshot_date", sort=True):
            t = pd.Timestamp(snapshot)
            if t.tzinfo is None:
                t = t.tz_localize("UTC")
            else:
                t = t.tz_convert("UTC")
            base = snapshot_rows[["visitorid"]].drop_duplicates().copy()
            base["snapshot_date"] = t
            base["customer_id"] = base.visitorid.astype("string")
            base["scenario_id"] = scenario_id

            pre = events.loc[events.event_time_utc < t]
            max_time = pre.groupby("visitorid", sort=False).event_time_utc.max().rename("feature_max_event_time_utc").reset_index()
            base = base.merge(max_time, on="visitorid", how="left")
            pre_weeks = pre.assign(_week=pre.event_time_utc.dt.normalize() - pd.to_timedelta(pre.event_time_utc.dt.dayofweek, unit="D"))
            active_weeks = pre_weeks.groupby("visitorid", sort=False)._week.nunique().rename("_active_weeks").reset_index()
            base = base.merge(active_weeks, on="visitorid", how="left")
            pre_counts = _event_counts(events, pd.Timestamp.min.tz_localize("UTC"), t)
            base = _merge_count(base, pre_counts, ["views", "carts", "purchases", "events"])
            base = base.merge(pre.groupby("visitorid", sort=False).itemid.nunique().rename("_distinct_items").reset_index(), on="visitorid", how="left")
            base["_distinct_items"] = base["_distinct_items"].fillna(0).astype("int64")

            for window in WINDOW_FEATURES:
                start = t - WEEK * window
                event_counts = _event_counts(events, start, t).rename(columns={
                    "views": f"feature_views_{window}w", "carts": f"feature_carts_{window}w",
                    "purchases": f"feature_purchases_{window}w", "events": f"feature_events_{window}w",
                })
                base = _merge_count(base, event_counts, [f"feature_{name}_{window}w" for name in ("views", "carts", "purchases", "events")])
                session_counts = _session_counts(sessions, start, t, f"{window}w").rename(columns={f"sessions_{window}w": f"feature_sessions_{window}w"})
                base = _merge_count(base, session_counts, [f"feature_sessions_{window}w"])

            four_week_start = t - WEEK * 4
            four_week_events = _events_in(events, four_week_start, t)
            active_days = four_week_events.assign(_day=four_week_events.event_time_utc.dt.normalize()).groupby("visitorid", sort=False)._day.nunique().rename("feature_active_days_4w").reset_index()
            base = base.merge(active_days, on="visitorid", how="left")
            base["feature_active_days_4w"] = base.feature_active_days_4w.fillna(0).astype("int32")

            baseline_start = t - WEEK * (b_weeks + o_weeks)
            observation_start = t - WEEK * o_weeks
            base_sessions = _session_counts(sessions, baseline_start, observation_start, "base")
            obs_sessions = _session_counts(sessions, observation_start, t, "obs")
            base = _merge_count(base, base_sessions, ["sessions_base"])
            base = _merge_count(base, obs_sessions, ["sessions_obs"])
            base["feature_baseline_sessions_per_week"] = base.sessions_base / b_weeks
            base["feature_observation_sessions_per_week"] = base.sessions_obs / o_weeks
            base["feature_baseline_events_per_week"] = _events_in(events, baseline_start, observation_start).groupby("visitorid", sort=False).size().reindex(base.visitorid, fill_value=0).to_numpy() / b_weeks
            base["feature_observation_events_per_week"] = _events_in(events, observation_start, t).groupby("visitorid", sort=False).size().reindex(base.visitorid, fill_value=0).to_numpy() / o_weeks
            denominator = base.feature_baseline_sessions_per_week
            base["feature_decay_ratio"] = (base.feature_observation_sessions_per_week / denominator).where(denominator.ne(0))
            base["feature_decay_ratio_is_null"] = base.feature_decay_ratio.isna()
            base["feature_eds"] = (1 - base.feature_decay_ratio).clip(lower=0)
            base["feature_eds_is_null"] = base.feature_eds.isna()

            x = np.arange(6, dtype=float)
            x_centered = x - x.mean()
            week_sessions = sessions.loc[(sessions.session_start_utc >= t - WEEK * 6) & (sessions.session_start_utc < t)].copy()
            week_sessions["_week_index"] = ((week_sessions.session_start_utc.dt.normalize() - pd.to_timedelta(week_sessions.session_start_utc.dt.dayofweek, unit="D") - (t - WEEK * 6)) / WEEK).astype(int)
            week_counts = week_sessions.groupby(["visitorid", "_week_index"], sort=False).size().unstack(fill_value=0).reindex(columns=range(6), fill_value=0)
            if week_counts.empty:
                slope_frame = pd.DataFrame(columns=["visitorid", "feature_slope_sessions_6w"])
            else:
                weekly_values = week_counts.to_numpy(dtype=float)
                slope = ((weekly_values - weekly_values.mean(axis=1, keepdims=True)) @ x_centered) / np.square(x_centered).sum()
                slope_frame = pd.DataFrame({"visitorid": week_counts.index, "feature_slope_sessions_6w": slope})
            base = base.merge(slope_frame, on="visitorid", how="left")
            base["feature_slope_sessions_6w_is_null"] = base.feature_slope_sessions_6w.isna()

            last_by_type = pre.groupby(["visitorid", "event_type"], observed=True, sort=False).event_time_utc.max().unstack()
            last_by_type = last_by_type.reindex(columns=EVENT_TYPES).astype("datetime64[ns, UTC]").rename(columns={
                "view": "_last_view", "addtocart": "_last_cart", "transaction": "_last_purchase",
            }).reset_index()
            base = base.merge(last_by_type, on="visitorid", how="left")
            for source, target in (("_last_view", "feature_days_since_last_view"), ("_last_cart", "feature_days_since_last_cart"), ("_last_purchase", "feature_days_since_last_purchase")):
                base[target] = (t - base[source]).dt.total_seconds() / 86_400
            base["feature_recency_days"] = (t - base.feature_max_event_time_utc).dt.total_seconds() / 86_400
            base["feature_frequency_events_per_active_week"] = base.events / base._active_weeks.replace(0, np.nan)
            base["feature_cart_to_view"] = (base.carts / base.views).where(base.views.ne(0))
            base["feature_cart_to_view_is_null"] = base.feature_cart_to_view.isna()
            base["feature_any_purchase_pre"] = base.purchases.gt(0)
            base["feature_n_distinct_items_pre"] = base._distinct_items
            base["feature_total_events_pre"] = base.events
            frames.append(base.reindex(columns=FEATURE_COLUMNS))
    result = pd.concat(frames, ignore_index=True).sort_values(["visitorid", "snapshot_date"], kind="mergesort").reset_index(drop=True)
    result["snapshot_index"] = result.groupby("visitorid", sort=False).cumcount().astype("int32")
    if result["feature_max_event_time_utc"].isna().any() or not (result.feature_max_event_time_utc < result.snapshot_date).all():
        raise AssertionError("pre-T feature boundary violation")
    return result
