import pandas as pd

from data.scripts.config import DEFAULT_CONFIG
from data.scripts.export_supplementary import _label_sensitivity


def test_label_sensitivity_keeps_censored_unknown_and_separates_no_purchase():
    labels = pd.DataFrame({
        "visitorid": [1, 2, 3], "snapshot_date": pd.to_datetime(["2015-06-15"] * 3, utc=True),
        "label_end_utc": pd.to_datetime(["2015-06-29", "2015-06-29", "2015-06-29"], utc=True),
        "future_events": [1, 1, 0], "future_sessions": [1, 1, 0], "future_purchases": [1, 0, 0],
    })
    features = pd.DataFrame({
        "visitorid": [1, 2, 3], "snapshot_date": labels.snapshot_date,
        "feature_baseline_sessions_per_week": [4., 4., 4.],
        "feature_observation_sessions_per_week": [1., 1., 1.],
        "feature_baseline_events_per_week": [4., 4., 4.],
        "feature_observation_events_per_week": [1., 1., 1.],
    })
    config = {**DEFAULT_CONFIG, "time": {**DEFAULT_CONFIG["time"], "observed_through": "2015-06-28T00:00:00Z"}}
    rows = _label_sensitivity(labels, features, config)
    session_half = next(row for row in rows if row["engagement_unit"] == "sessions" and row["theta"] == .5)
    assert session_half["counts"] == {"unknown": 3}
    assert session_half["no_purchase_variant_counts"] == {"unknown": 3}


def test_mature_rows_without_active_label_do_not_raise_key_error():
    labels = pd.DataFrame({
        "visitorid": [1], "snapshot_date": pd.to_datetime(["2015-06-15"], utc=True),
        "label_end_utc": pd.to_datetime(["2015-06-29"], utc=True),
        "future_events": [1], "future_sessions": [1], "future_purchases": [1],
    })
    features = pd.DataFrame({
        "visitorid": [1], "snapshot_date": labels.snapshot_date,
        "feature_baseline_sessions_per_week": [4.], "feature_observation_sessions_per_week": [1.],
        "feature_baseline_events_per_week": [4.], "feature_observation_events_per_week": [1.],
    })
    rows = _label_sensitivity(labels, features, DEFAULT_CONFIG)
    session_half = next(row for row in rows if row["engagement_unit"] == "sessions" and row["theta"] == .5)
    assert session_half["no_purchase_variant_counts"] == {"active": 1}
