from __future__ import annotations

import pandas as pd


def aggregate_user_week(events_with_session: pd.DataFrame) -> pd.DataFrame:
    events = events_with_session.copy()
    if "session_week_start" not in events:
        session_week = events.groupby("session_id", sort=False)["event_time_utc"].transform("min")
        events["session_week_start"] = session_week.dt.normalize() - pd.to_timedelta(session_week.dt.dayofweek, unit="D")
    events["_event_date"] = events["event_time_utc"].dt.normalize()
    for event_type, column in (("view", "views"), ("addtocart", "carts"), ("transaction", "purchases")):
        events[column] = events["event_type"].eq(event_type).astype("int32")
    weekly = (
        events.groupby(["visitorid", "session_week_start"], sort=True, observed=True)
        .agg(
            views=("views", "sum"),
            carts=("carts", "sum"),
            purchases=("purchases", "sum"),
            events=("event_time_utc", "size"),
            sessions=("session_id", "nunique"),
            active_days=("_event_date", "nunique"),
        )
        .reset_index()
        .rename(columns={"session_week_start": "week_start"})
    )
    for column in ("views", "carts", "purchases", "events", "sessions", "active_days"):
        weekly[column] = weekly[column].astype("int32")
    return weekly
