from __future__ import annotations

import pandas as pd


def _week_start(series: pd.Series) -> pd.Series:
    return series.dt.normalize() - pd.to_timedelta(series.dt.dayofweek, unit="D")


def build_sessions(events: pd.DataFrame, gap_minutes: int = 30) -> tuple[pd.DataFrame, pd.DataFrame]:
    if gap_minutes <= 0:
        raise ValueError("session gap must be positive")
    ordered = events.sort_values(["visitorid", "event_time_utc", "source_row"], kind="mergesort").copy().reset_index(drop=True)
    gap = ordered.groupby("visitorid", sort=False)["event_time_utc"].diff()
    ordered["_new_session"] = gap.isna() | gap.gt(pd.Timedelta(gap_minutes * 60, unit="s"))
    ordered["_session_index"] = ordered.groupby("visitorid", sort=False)["_new_session"].cumsum().astype("int32") - 1
    ordered["session_id"] = ordered["visitorid"].astype("string") + "-" + ordered["_session_index"].astype("string")
    ordered["_event_date"] = ordered["event_time_utc"].dt.normalize()
    ordered["_session_week"] = _week_start(ordered["event_time_utc"])

    for event_type, column in (("view", "n_views"), ("addtocart", "n_carts"), ("transaction", "n_purchases")):
        ordered[column] = ordered["event_type"].eq(event_type).astype("int32")
    sessions = (
        ordered.groupby(["visitorid", "session_id"], sort=False, observed=True)
        .agg(
            session_start_utc=("event_time_utc", "min"),
            session_end_utc=("event_time_utc", "max"),
            n_events=("event_time_utc", "size"),
            n_views=("n_views", "sum"),
            n_carts=("n_carts", "sum"),
            n_purchases=("n_purchases", "sum"),
            active_days=("_event_date", "nunique"),
        )
        .reset_index()
    )
    sessions["session_week_start"] = _week_start(sessions["session_start_utc"])
    ordered = ordered.drop(columns=["_new_session", "_session_index", "_event_date"])
    return sessions, ordered
