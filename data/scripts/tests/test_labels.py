import pandas as pd

from data.scripts.config import DEFAULT_CONFIG
from data.scripts.labels import build_labels, minimal_labels
from data.scripts.sessions import build_sessions


def _case(observed_through="2015-09-14T00:00:00Z"):
    t = pd.Timestamp("2015-06-15T00:00:00Z")
    times = [
        "2015-06-01T00:00:00Z",
        "2015-06-14T23:59:59.999Z",
        "2015-06-15T00:00:00Z",
        "2015-06-28T23:59:59.999Z",
        "2015-06-29T00:00:00Z",
    ]
    events = pd.DataFrame(
        {
            "visitorid": pd.Series([7] * len(times), dtype="int64"),
            "event_time_utc": pd.to_datetime(times, utc=True, format="mixed"),
            "event_type": ["view"] * len(times),
            "itemid": pd.Series(range(10, 10 + len(times)), dtype="int64"),
            "transactionid": pd.Series([pd.NA] * len(times), dtype="Int64"),
            "source_row": pd.Series(range(2, 2 + len(times)), dtype="int64"),
            "is_exact_duplicate": [False] * len(times),
            "is_extreme_visitor": [False] * len(times),
        }
    )
    sessions, _ = build_sessions(events, 30)
    cohort = pd.DataFrame({"visitorid": pd.Series([7], dtype="int64"), "snapshot_date": [t], "scenario_id": ["b4_o2_c2"], "history_eligible": [True]})
    features = pd.DataFrame({
        "visitorid": pd.Series([7], dtype="int64"),
        "snapshot_date": [t],
        "scenario_id": ["b4_o2_c2"],
        "feature_baseline_sessions_per_week": [4.0],
        "feature_observation_sessions_per_week": [1.0],
        "feature_baseline_events_per_week": [0.5],
        "feature_observation_events_per_week": [2.0],
    })
    config = {**DEFAULT_CONFIG, "time": {**DEFAULT_CONFIG["time"], "observed_through": observed_through}}
    return t, events, sessions, cohort, features, config


def test_label_T_and_horizon_boundaries_are_half_open():
    _, events, sessions, cohort, features, config = _case()
    labels = build_labels(events, sessions, cohort, features, config, theta=0.5)
    row = labels.iloc[0]
    assert row.future_events == 2
    assert row.label_status == "ghost"
    assert row.target_ghost == 1
    assert row.future_events == int(((events.event_time_utc >= row.snapshot_date) & (events.event_time_utc < row.label_end_utc)).sum())
    assert list(minimal_labels(labels).columns) == ["visitorid", "snapshot_date", "label_end", "label_status", "target_ghost"]


def test_censored_confirmation_is_unknown_with_null_targets():
    _, events, sessions, cohort, features, config = _case("2015-06-22T00:00:00Z")
    labels = build_labels(events, sessions, cohort, features, config, theta=0.5)
    row = labels.iloc[0]
    assert row.label_status == "unknown"
    assert pd.isna(row.target_ghost)
    assert pd.isna(row.target_disengaged)
    assert not row.horizon_mature


def test_event_engagement_sensitivity_uses_event_baseline_rate():
    _, events, sessions, cohort, features, config = _case()
    labels = build_labels(events, sessions, cohort, features, config, theta=0.5, engagement_unit="events")
    assert labels.iloc[0].label_status == "active"
