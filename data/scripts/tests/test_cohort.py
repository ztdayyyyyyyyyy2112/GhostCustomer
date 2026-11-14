from pathlib import Path

import pytest

from data.scripts.clean import clean_events
from data.scripts.config import DEFAULT_CONFIG
from data.scripts.cohort import exclusion_reason
from data.scripts.cohort import build_cohort


ROOT = Path(__file__).resolve().parents[3]


def test_cohort_exclusion_precedence():
    assert exclusion_reason(2, 1, 0, 0, False, 5, 2, "research") == "insufficient_events"
    assert exclusion_reason(6, 1, 0, 0, False, 5, 2, "research") == "insufficient_active_weeks"
    assert exclusion_reason(6, 2, 0, 3, False, 5, 2, "audit_compat") == "no_baseline_activity"
    assert exclusion_reason(6, 2, 2, 0, False, 5, 2, "research") == "no_observation_activity"
    assert exclusion_reason(6, 2, 2, 3, True, 5, 2, "audit_compat") == "immature_horizon"
    assert exclusion_reason(6, 2, 2, 3, False, 5, 2, "audit_compat") == "ok"


@pytest.mark.skipif(not (ROOT / "data/raw/events.csv").exists(), reason="raw Retailrocket data is not committed")
def test_audit_compat_matches_golden_counts():
    events = clean_events(ROOT / "data/raw/events.csv")
    cohort = build_cohort(events, DEFAULT_CONFIG, DEFAULT_CONFIG["scenarios"][0], "audit_compat")
    complete = cohort.loc[cohort["eligible_audit"]]
    assert len(complete) == 85_899
    assert complete.visitorid.nunique() == 24_768
    assert int((complete.groupby("visitorid").size() > 1).sum()) == 20_989
    assert int((~cohort.loc[cohort.history_eligible, "horizon_mature"]).sum()) == 11_590
