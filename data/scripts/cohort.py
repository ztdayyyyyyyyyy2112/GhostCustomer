from __future__ import annotations

from collections.abc import Iterator

import numpy as np
import pandas as pd

WEEK = pd.Timedelta(7, unit="d")


def exclusion_reason(history_events, active_weeks, baseline_events, observation_events, immature, min_events, min_active_weeks, mode):
    if history_events < min_events:
        return "insufficient_events"
    if active_weeks < min_active_weeks:
        return "insufficient_active_weeks"
    if baseline_events == 0:
        return "no_baseline_activity"
    if mode == "research" and observation_events == 0:
        return "no_observation_activity"
    if immature:
        return "immature_horizon"
    return "ok"


def _utc(value) -> pd.Timestamp:
    return pd.Timestamp(value).tz_localize("UTC") if pd.Timestamp(value).tzinfo is None else pd.Timestamp(value).tz_convert("UTC")


def _weekly_events(events: pd.DataFrame) -> pd.DataFrame:
    data = events.assign(week_start=events["event_time_utc"].dt.normalize() - pd.to_timedelta(events["event_time_utc"].dt.dayofweek, unit="D"))
    return data.groupby(["visitorid", "week_start"], sort=True, observed=True).size().rename("events").reset_index()


def iter_cohort_snapshots(events: pd.DataFrame, config: dict, scenario: dict) -> Iterator[pd.DataFrame]:
    baseline_weeks = int(scenario["baseline_weeks"])
    observation_weeks = int(scenario["observation_weeks"])
    confirmation_weeks = int(scenario["confirmation_weeks"])
    first_week = _utc(config["time"]["first_full_week"])
    observed_through = _utc(config["time"]["observed_through"])
    full_weeks = int((observed_through - first_week) / WEEK)
    weekly = _weekly_events(events)
    min_events = min(config["eligibility"]["min_pre_events"])
    min_active_weeks = min(config["eligibility"]["min_active_weeks"])

    for t_index in range(baseline_weeks + observation_weeks, full_weeks + 1):
        snapshot = first_week + WEEK * t_index
        base_start = snapshot - WEEK * (baseline_weeks + observation_weeks)
        observation_start = snapshot - WEEK * observation_weeks
        history = weekly.loc[(weekly.week_start >= base_start) & (weekly.week_start < snapshot)]
        baseline = history.loc[history.week_start < observation_start].groupby("visitorid", sort=False).events.sum().rename("baseline_events")
        observation = history.loc[history.week_start >= observation_start].groupby("visitorid", sort=False).events.sum().rename("observation_events")
        history_summary = history.groupby("visitorid", sort=False).agg(history_events=("events", "sum"), active_weeks=("week_start", "nunique"))
        candidates = events.loc[events.event_time_utc < snapshot, "visitorid"].drop_duplicates().to_frame()
        trace = candidates.merge(history_summary, on="visitorid", how="left").merge(baseline, on="visitorid", how="left").merge(observation, on="visitorid", how="left")
        for column in ("history_events", "active_weeks", "baseline_events", "observation_events"):
            trace[column] = trace[column].fillna(0).astype("int32")
        label_end = snapshot + WEEK * confirmation_weeks
        immature = label_end > observed_through
        trace["snapshot_date"] = snapshot
        trace["label_end_utc"] = label_end
        trace["scenario_id"] = scenario["id"]
        trace["history_eligible"] = (trace.history_events >= min_events) & (trace.active_weeks >= min_active_weeks) & (trace.baseline_events > 0)
        trace["horizon_mature"] = not immature
        insufficient_events = trace.history_events.lt(min_events)
        insufficient_weeks = trace.active_weeks.lt(min_active_weeks)
        no_baseline = trace.baseline_events.eq(0)
        no_observation = trace.observation_events.eq(0)
        not_mature = pd.Series(immature, index=trace.index)
        audit_reason = np.select(
            [insufficient_events, insufficient_weeks, no_baseline, not_mature],
            ["insufficient_events", "insufficient_active_weeks", "no_baseline_activity", "immature_horizon"],
            default="ok",
        )
        research_reason = np.select(
            [insufficient_events, insufficient_weeks, no_baseline, no_observation, not_mature],
            ["insufficient_events", "insufficient_active_weeks", "no_baseline_activity", "no_observation_activity", "immature_horizon"],
            default="ok",
        )
        trace["exclusion_reason_audit"] = audit_reason
        trace["exclusion_reason_research"] = research_reason
        trace["eligible_audit"] = trace.exclusion_reason_audit.eq("ok")
        trace["eligible_research"] = trace.exclusion_reason_research.eq("ok")
        yield trace


def build_cohort(events: pd.DataFrame, config: dict, scenario: dict, mode: str = "audit_compat") -> pd.DataFrame:
    if mode not in {"audit_compat", "research"}:
        raise ValueError(f"unknown cohort mode: {mode}")
    eligible_column = "eligible_audit" if mode == "audit_compat" else "eligible_research"
    frames = [trace.loc[trace["history_eligible"]].copy() for trace in iter_cohort_snapshots(events, config, scenario)]
    result = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    result["eligible"] = result[eligible_column]
    result["exclusion_reason"] = result[f"exclusion_reason_{'audit' if mode == 'audit_compat' else 'research'}"]
    result["eligibility_mode"] = mode
    return result
