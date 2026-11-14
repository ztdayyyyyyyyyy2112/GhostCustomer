import pandas as pd

from data.scripts.sessions import build_sessions
from data.scripts.aggregate import aggregate_user_week


def test_session_gap_boundary_and_cross_week_assignment():
    events = pd.DataFrame(
        {
            "visitorid": pd.Series([1, 1, 1], dtype="int64"),
            "event_time_utc": pd.to_datetime(["2015-05-03T23:50:00Z", "2015-05-04T00:10:00Z", "2015-05-04T00:40:01Z"], utc=True),
            "event_type": ["view", "addtocart", "view"],
            "itemid": pd.Series([1, 2, 3], dtype="int64"),
            "transactionid": pd.Series([pd.NA, pd.NA, pd.NA], dtype="Int64"),
            "source_row": pd.Series([2, 3, 4], dtype="int64"),
            "is_exact_duplicate": [False, False, False],
            "is_extreme_visitor": [False, False, False],
        }
    )
    sessions, assigned = build_sessions(events, gap_minutes=30)
    assert assigned["session_id"].nunique() == 2
    assert assigned.loc[0, "session_id"] == assigned.loc[1, "session_id"]
    assert assigned.loc[1, "session_id"] != assigned.loc[2, "session_id"]
    assert sessions.iloc[0]["session_start_utc"] == pd.Timestamp("2015-05-03T23:50:00Z")
    weekly = aggregate_user_week(assigned)
    assert weekly["sessions"].sum() == len(sessions)
    assert weekly["events"].sum() == len(events)
    assert weekly.loc[weekly["week_start"] == pd.Timestamp("2015-04-27T00:00:00Z"), "events"].sum() == 2
