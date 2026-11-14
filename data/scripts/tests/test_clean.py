from pathlib import Path

import pytest

from data.scripts.clean import clean_events


def test_event_map_duplicate_flag_and_typed_ids(tmp_path: Path):
    raw = tmp_path / "events.csv"
    raw.write_text(
        "timestamp,visitorid,event,itemid,transactionid\n"
        "1433221332117,7,view,355908,\n"
        "1433221332117,7,view,355908,\n"
        "1433224214164,8,transaction,248676,44\n",
        encoding="utf-8",
    )
    cleaned = clean_events(raw)
    assert len(cleaned) == 3
    assert cleaned["visitorid"].dtype == "int64"
    assert cleaned["itemid"].dtype == "int64"
    assert str(cleaned["transactionid"].dtype) == "Int64"
    assert cleaned["event_type"].tolist() == ["view", "view", "transaction"]
    assert cleaned["is_exact_duplicate"].tolist() == [False, True, False]
    assert cleaned["transactionid"].isna().sum() == 2


def test_unknown_event_fails_without_silently_dropping_row(tmp_path: Path):
    raw = tmp_path / "events.csv"
    raw.write_text("timestamp,visitorid,event,itemid,transactionid\n1,1,click,2,\n", encoding="utf-8")
    with pytest.raises(ValueError, match="unknown event"):
        clean_events(raw)
