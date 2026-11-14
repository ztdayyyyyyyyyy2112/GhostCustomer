import math

import pandas as pd
import pytest

from data.scripts.run_pipeline import descriptive_groups


def test_descriptive_groups_report_sd_and_missingness():
    rows = pd.DataFrame(
        {
            "label_status": ["ghost", "ghost", "ghost", "active"],
            "sessions": [1, 3, None, 5],
            "recency_days": [2.0, 4.0, None, 6.0],
            "decay": [None, None, None, 0.5],
        }
    )

    groups = descriptive_groups(rows, ["sessions", "recency_days", "decay"])
    ghost_sessions = next(group for group in groups if group["name"] == "ghost" and group["metric"] == "sessions")
    ghost_recency = next(group for group in groups if group["name"] == "ghost" and group["metric"] == "recency_days")
    ghost_decay = next(group for group in groups if group["name"] == "ghost" and group["metric"] == "decay")

    assert ghost_sessions["n"] == 2
    assert ghost_sessions["n_total"] == 3
    assert ghost_sessions["missing_n"] == 1
    assert ghost_sessions["missing_rate"] == 1 / 3
    assert ghost_sessions["sd"] == pytest.approx(math.sqrt(2))
    assert ghost_recency["unit"] == "days"
    assert ghost_decay["n"] == 0
    assert ghost_decay["missing_n"] == 3
    assert ghost_decay["missing_rate"] == 1
    assert ghost_decay["mean"] is None
    assert ghost_decay["sd"] is None
