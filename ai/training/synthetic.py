"""Synthetic Retailrocket-format events for tests and dry runs ONLY.

The rows are generated, not observed. They let the AI pipeline run end to end
through Lâm's real data functions (clean -> sessions -> cohort -> features ->
labels) without the licensed raw file. Never report metrics computed on them.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

START = pd.Timestamp("2015-05-04", tz="UTC")
END = pd.Timestamp("2015-09-14", tz="UTC")


def make_events(n_visitors: int = 600, seed: int = 3013) -> pd.DataFrame:
    """Raw events with columns timestamp,visitorid,event,itemid,transactionid."""
    rng = np.random.default_rng(seed)
    days = (END - START).days
    rows = []
    txn = 1
    for vid in range(1, n_visitors + 1):
        base = rng.gamma(2.0, 1.2)                # sessions per week at start
        decay_day = rng.integers(20, days) if rng.random() < 0.45 else None
        decay_to = rng.uniform(0.0, 0.5)
        for day in range(days):
            rate = base / 7
            if decay_day is not None and day >= decay_day:
                rate *= decay_to
            for _ in range(rng.poisson(rate)):
                t0 = START + pd.Timedelta(days=day, seconds=int(rng.integers(0, 86_000)))
                n_views = 1 + rng.poisson(2)
                for k in range(n_views):
                    ts = t0 + pd.Timedelta(minutes=2 * k)
                    item = int(rng.integers(1, 400))
                    rows.append((ts, vid, "view", item, pd.NA))
                    if rng.random() < 0.08:
                        rows.append((ts + pd.Timedelta(seconds=30), vid, "addtocart", item, pd.NA))
                        if rng.random() < 0.35:
                            rows.append((ts + pd.Timedelta(seconds=90), vid, "transaction", item, txn))
                            txn += 1
    df = pd.DataFrame(rows, columns=["ts", "visitorid", "event", "itemid", "transactionid"])
    df = df[df.ts < END]
    epoch = pd.Timestamp("1970-01-01", tz="UTC")
    df.insert(0, "timestamp", ((df.pop("ts") - epoch) // pd.Timedelta(milliseconds=1)).astype("int64"))
    df["transactionid"] = df["transactionid"].astype("Int64")
    return df.reset_index(drop=True)


def build_processed(n_visitors: int = 600, seed: int = 3013, workdir: Path | None = None):
    """Run Lâm's pipeline functions on synthetic events.

    Returns (features, labels) DataFrames with the real processed schema.
    """
    import tempfile

    from data.scripts.clean import clean_events
    from data.scripts.cohort import iter_cohort_snapshots
    from data.scripts.config import load_config
    from data.scripts.features import build_features
    from data.scripts.labels import build_labels
    from data.scripts.sessions import build_sessions

    config = load_config()
    workdir = Path(workdir or tempfile.mkdtemp())
    raw = workdir / "events.csv"
    make_events(n_visitors, seed).to_csv(raw, index=False)
    events = clean_events(raw, config["extreme_visitor_quantile"])
    # pandas>=3 shim: the pinned pipeline (pandas 2.3) tolerates a categorical
    # event_type in label aggregation; newer pandas does not. Values are unchanged.
    events["event_type"] = events["event_type"].astype(str)
    sessions, _ = build_sessions(events, config["sessions"]["preferred_gap_minutes"])
    scenario_id = config["preferred_scenario_id"].split("_min")[0]
    scenario = next(s for s in config["scenarios"] if s["id"] == scenario_id)
    trace = pd.concat(iter_cohort_snapshots(events, config, scenario), ignore_index=True)
    primary = trace.loc[trace.history_eligible].copy()
    primary["eligible"] = primary["eligible_audit"]
    primary["exclusion_reason"] = primary["exclusion_reason_audit"]
    features = build_features(events, sessions, primary, config)
    labels = build_labels(events, sessions, primary, features, config)
    return features, labels


if __name__ == "__main__":
    f, l = build_processed()
    print(f.shape, l.shape)
    print(l.label_status.value_counts())
    print(f.snapshot_date.value_counts().sort_index())
