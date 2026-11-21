from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd


if len(sys.argv) not in (2, 3):
    raise SystemExit("Usage: python retailrocket_audit.py /path/to/events.csv [result.json]")
SOURCE = Path(sys.argv[1])
RESULT = Path(sys.argv[2]) if len(sys.argv) == 3 else Path("retailrocket_audit.json")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


data = pd.read_csv(
    SOURCE,
    dtype={
        "timestamp": "int64",
        "visitorid": "int32",
        "event": "category",
        "itemid": "int32",
        "transactionid": "float64",
    },
)
dates = pd.to_datetime(data["timestamp"], unit="ms", utc=True)
minimum, maximum = dates.min(), dates.max()
week_start = (dates - pd.to_timedelta(dates.dt.weekday, unit="D")).dt.normalize()
first_monday = minimum.normalize() - pd.Timedelta(days=minimum.weekday())
if minimum > first_monday:
    first_monday += pd.Timedelta(weeks=1)
last_monday = maximum.normalize() - pd.Timedelta(days=maximum.weekday())
full_weeks = int((last_monday - first_monday) / pd.Timedelta(weeks=1))
week_index = ((week_start - first_monday) / pd.Timedelta(weeks=1)).astype("int16")
full = data.loc[(week_index >= 0) & (week_index < full_weeks), ["visitorid"]].copy()
full["week"] = week_index[(week_index >= 0) & (week_index < full_weeks)].to_numpy()
weekly = full.groupby(["visitorid", "week"], observed=True).size().unstack(fill_value=0)
weekly = weekly.reindex(columns=range(full_weeks), fill_value=0).astype("int32")
ids = weekly.index.to_numpy()
array = weekly.to_numpy()
del full, weekly

configurations = [(4, 2, 2), (4, 3, 2), (6, 2, 4)]
rows = []
for baseline, observation, confirmation in configurations:
    for threshold in (5, 10):
        eligible_ids = []
        eligible_snapshots = 0
        baseline_snapshots = 0
        future_zero = 0
        observation_zero = 0
        both_periods_positive = 0
        censored = 0
        complete_t = 0
        per_snapshot = []
        first_seen = np.zeros(len(ids), dtype=bool)
        first_snapshot_zero_future = 0
        first_snapshot_both_periods_positive = 0
        for t in range(baseline + observation, full_weeks + 1):
            history = array[:, t - baseline - observation : t]
            history_count = history.sum(axis=1)
            active_weeks = np.count_nonzero(history, axis=1)
            base_count = history[:, :baseline].sum(axis=1)
            obs_count = history[:, baseline:].sum(axis=1)
            basic = (history_count >= threshold) & (active_weeks >= 2)
            eligible = basic & (base_count > 0)
            if t + confirmation > full_weeks:
                censored += int(np.count_nonzero(eligible))
                continue
            complete_t += 1
            eligible_snapshots += int(np.count_nonzero(basic))
            baseline_snapshots += int(np.count_nonzero(eligible))
            eligible_ids.append(ids[eligible])
            future = array[:, t : t + confirmation].sum(axis=1)
            first_at_t = eligible & ~first_seen
            first_snapshot_zero_future += int(np.count_nonzero(first_at_t & (future == 0)))
            first_snapshot_both_periods_positive += int(np.count_nonzero(first_at_t & (obs_count > 0) & (future > 0)))
            first_seen |= eligible
            zero_future_at_t = int(np.count_nonzero(eligible & (future == 0)))
            future_zero += zero_future_at_t
            observation_zero += int(np.count_nonzero(eligible & (obs_count == 0)))
            both_periods_positive += int(np.count_nonzero(eligible & (future > 0) & (obs_count > 0)))
            per_snapshot.append(
                {
                    "snapshot_date": (first_monday + pd.Timedelta(weeks=t)).date().isoformat(),
                    "eligible_with_baseline": int(np.count_nonzero(eligible)),
                    "zero_future_events": zero_future_at_t,
                }
            )
        combined = np.concatenate(eligible_ids) if eligible_ids else np.array([], dtype=ids.dtype)
        distinct, frequency = np.unique(combined, return_counts=True)
        rows.append(
            {
                "baseline_weeks": baseline,
                "observation_weeks": observation,
                "confirmation_weeks": confirmation,
                "history_min_events": threshold,
                "history_min_active_weeks": 2,
                "complete_snapshot_dates": complete_t,
                "eligible_snapshots_before_baseline_filter": eligible_snapshots,
                "eligible_snapshots_with_baseline": baseline_snapshots,
                "unique_eligible_visitors": int(distinct.size),
                "visitors_with_multiple_snapshots": int(np.count_nonzero(frequency > 1)),
                "first_snapshot_zero_future": first_snapshot_zero_future,
                "first_snapshot_activity_in_both_periods": first_snapshot_both_periods_positive,
                "snapshots_with_zero_future_events": future_zero,
                "snapshots_with_zero_observation_events": observation_zero,
                "snapshots_with_activity_in_observation_and_confirmation": both_periods_positive,
                "right_censored_candidate_snapshots": censored,
                "per_snapshot": per_snapshot,
            }
        )

weekly_coverage = []
for week in range(full_weeks):
    column = array[:, week]
    weekly_coverage.append(
        {
            "week_start": (first_monday + pd.Timedelta(weeks=week)).date().isoformat(),
            "events": int(column.sum()),
            "active_visitors": int(np.count_nonzero(column)),
        }
    )

result = {
    "source": str(SOURCE),
    "sha256": sha256(SOURCE),
    "file_bytes": SOURCE.stat().st_size,
    "rows": int(len(data)),
    "columns": list(data.columns),
    "missing_by_column": {key: int(value) for key, value in data.isna().sum().items()},
    "duplicate_full_rows": int(data.duplicated().sum()),
    "unique_visitors": int(data.visitorid.nunique()),
    "event_counts": {str(key): int(value) for key, value in data.event.value_counts().items()},
    "min_utc": minimum.isoformat(),
    "max_utc": maximum.isoformat(),
    "first_full_week_start": first_monday.date().isoformat(),
    "last_full_week_end_exclusive": last_monday.date().isoformat(),
    "full_week_count": full_weeks,
    "full_week_coverage": weekly_coverage,
    "candidate_windows": rows,
}
RESULT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"Audited {result['rows']:,} events and {result['unique_visitors']:,} visitors. Wrote {RESULT}.")
