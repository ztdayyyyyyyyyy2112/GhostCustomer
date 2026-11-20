from __future__ import annotations

import pandas as pd

from research.regression.logistic_inference import split_time


def test_two_week_labels_are_purged_before_each_evaluation_origin():
    dates = pd.date_range("2015-06-15", periods=12, freq="W-MON", tz="UTC")
    rows = []
    for week, snapshot in enumerate(dates):
        for visitor in range(60):
            rows.append({
                "visitorid": f"{week}-{visitor}", "snapshot_date": snapshot,
                "label_end": snapshot + pd.Timedelta(weeks=2),
                "target_ghost": visitor % 3 == 0,
            })
    train, validation, test = split_time(pd.DataFrame(rows))
    assert min(map(len, (train, validation, test))) >= 20
    assert train.label_end.max() < validation.snapshot_date.min()
    assert validation.label_end.max() < test.snapshot_date.min()
    assert not set(train.visitorid) & set(validation.visitorid)
    assert not set(validation.visitorid) & set(test.visitorid)
