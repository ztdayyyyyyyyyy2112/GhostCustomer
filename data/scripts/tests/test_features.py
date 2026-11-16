import pandas as pd

from data.scripts.config import DEFAULT_CONFIG, FEATURE_COLUMNS
from data.scripts.features import build_features
from data.scripts.sessions import build_sessions


def _fixture():
    t = pd.Timestamp("2015-06-15T00:00:00Z")
    events = pd.DataFrame(
        {
            "visitorid": pd.Series([41, 41, 41], dtype="int64"),
            "event_time_utc": pd.to_datetime(["2015-06-14T22:00:00Z", "2015-06-15T00:00:00Z", "2015-06-15T01:00:00Z"], utc=True),
            "event_type": ["view", "addtocart", "transaction"],
            "itemid": pd.Series([11, 12, 13], dtype="int64"),
            "transactionid": pd.Series([pd.NA, pd.NA, 7], dtype="Int64"),
            "source_row": pd.Series([2, 3, 4], dtype="int64"),
            "is_exact_duplicate": [False, False, False],
            "is_extreme_visitor": [False, False, False],
        }
    )
    sessions, _ = build_sessions(events, 30)
    cohort = pd.DataFrame({"visitorid": pd.Series([41], dtype="int64"), "snapshot_date": [t], "scenario_id": ["b4_o2_c2"], "history_eligible": [True]})
    return t, events, sessions, cohort


def test_features_exclude_event_at_T_and_feature_max_time_is_before_T():
    t, events, sessions, cohort = _fixture()
    result = build_features(events, sessions, cohort, DEFAULT_CONFIG)
    row = result.iloc[0]
    assert tuple(result.columns) == FEATURE_COLUMNS
    assert row.feature_views_1w == 1
    assert row.feature_carts_1w == 0
    assert row.feature_purchases_1w == 0
    assert row.feature_total_events_pre == 1
    assert row.feature_baseline_events_per_week == 0.0
    assert row.feature_observation_events_per_week == 0.5
    assert row.feature_max_event_time_utc < t


def test_feature_truncation_invariance():
    t, events, sessions, cohort = _fixture()
    full = build_features(events, sessions, cohort, DEFAULT_CONFIG)
    truncated = events.loc[events.event_time_utc < t].copy()
    truncated_sessions, _ = build_sessions(truncated, 30)
    cut = build_features(truncated, truncated_sessions, cohort, DEFAULT_CONFIG)
    pd.testing.assert_frame_equal(full, cut)
