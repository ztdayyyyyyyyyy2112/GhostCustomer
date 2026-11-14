import pandas as pd

from data.scripts.export_supplementary import _label_sensitivity


def test_label_sensitivity_keeps_censored_unknown_and_separates_no_purchase():
    labels = pd.DataFrame({
        "visitorid": [1, 2, 3], "snapshot_date": pd.to_datetime(["2015-06-15"] * 3, utc=True),
        "future_events": [1, 1, 0], "future_sessions": [1, 1, 0], "future_purchases": [1, 0, 0],
        "horizon_mature": [True, True, False],
    })
    features = pd.DataFrame({
        "visitorid": [1, 2, 3], "snapshot_date": labels.snapshot_date,
        "feature_baseline_sessions_per_week": [4., 4., 4.],
        "feature_observation_sessions_per_week": [1., 1., 1.],
        "feature_baseline_events_per_week": [4., 4., 4.],
        "feature_observation_events_per_week": [1., 1., 1.],
    })
    rows = _label_sensitivity(labels, features)
    session_half = next(row for row in rows if row["engagement_unit"] == "sessions" and row["theta"] == .5)
    assert session_half["counts"] == {"ghost": 2, "unknown": 1}
    assert session_half["no_purchase_variant_counts"] == {"ghost": 1, "active": 1, "unknown": 1}
