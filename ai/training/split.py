"""Visitor-aware temporal split with label purging (AI-03, proposal for D-05).

Rules
1. Time: train snapshots < validation snapshots < test snapshots. The last
   `test_weeks` mature snapshot weeks are the test period.
2. Purge: every label window [T, label_end) of an earlier split ends strictly
   before the first snapshot of the next split, so no label period overlaps
   (same strict check as research/baselines/decision_tree.py).
3. Visitors: each visitor is hashed (SHA-256 of seed + customer_id) into
   exactly one bucket (train / validation / test); a bucket only contributes
   rows inside its own period. No visitor appears in two splits, and the
   bucket choice does not depend on the visitor's behaviour.
4. Deterministic: same input + seed -> same split. The manifest records the
   dates, counts, prevalence and a hash of the row assignment.
"""
from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass

import pandas as pd

from . import config

SPLITS = ("train", "validation", "test")


@dataclass(frozen=True)
class SplitPlan:
    train_end: str          # last train snapshot (inclusive), ISO date
    val_start: str
    val_end: str
    test_start: str
    test_end: str
    visitor_fractions: tuple[float, float, float]
    seed: int
    version: str
    visitor_disjoint: bool = True   # False = time-only sensitivity run (not for the shared benchmark)


def _bucket(customer_ids: pd.Series, fractions, seed: int) -> pd.Series:
    if abs(sum(fractions) - 1) > 1e-9 or min(fractions) <= 0:
        raise ValueError("visitor_fractions must be positive and sum to 1")
    cut1, cut2 = fractions[0], fractions[0] + fractions[1]

    def one(cid: str) -> str:
        h = int(hashlib.sha256(f"{seed}:{cid}".encode()).hexdigest()[:12], 16) / 16**12
        return "train" if h < cut1 else "validation" if h < cut2 else "test"

    uniq = pd.Series(customer_ids.unique())
    mapping = dict(zip(uniq, uniq.map(one)))
    return customer_ids.map(mapping)


def plan_split(data: pd.DataFrame, val_weeks: int | None = None, test_weeks: int | None = None,
               visitor_fractions=None, seed: int = config.SEED, visitor_disjoint: bool = True) -> SplitPlan:
    """Pick period boundaries from the distinct mature snapshot dates."""
    val_weeks = val_weeks or config.SPLIT_DEFAULTS["val_weeks"]
    test_weeks = test_weeks or config.SPLIT_DEFAULTS["test_weeks"]
    fractions = tuple(visitor_fractions or config.SPLIT_DEFAULTS["visitor_fractions"])
    dates = sorted(data["snapshot_date"].unique())
    horizon = (data["label_end_utc"] - data["snapshot_date"]).max()
    if len(dates) < 3:
        raise ValueError("Need at least 3 snapshot dates")
    test_dates = dates[-test_weeks:]
    test_start = pd.Timestamp(test_dates[0])
    # validation rows must have label_end < test_start
    val_pool = [d for d in dates if pd.Timestamp(d) + horizon < test_start]
    if len(val_pool) < val_weeks + 1:
        raise ValueError("Not enough snapshot weeks for train/validation/test with purging")
    val_dates = val_pool[-val_weeks:]
    val_start = pd.Timestamp(val_dates[0])
    train_pool = [d for d in dates if pd.Timestamp(d) + horizon < val_start]
    if not train_pool:
        raise ValueError("No training weeks left after purging")
    fmt = lambda d: pd.Timestamp(d).strftime("%Y-%m-%d")  # noqa: E731
    kind = "visitor-temporal-v1" if visitor_disjoint else "temporal-only-v1"
    buckets = f"_f{'-'.join(str(int(round(f * 100))) for f in fractions)}" if visitor_disjoint else ""
    version = f"{kind}_tr{fmt(train_pool[-1])}_va{fmt(val_start)}_te{fmt(test_start)}{buckets}_s{seed}"
    return SplitPlan(fmt(train_pool[-1]), fmt(val_start), fmt(val_dates[-1]), fmt(test_start),
                     fmt(test_dates[-1]), fractions, seed, version, visitor_disjoint)


def assign_split(data: pd.DataFrame, plan: SplitPlan) -> pd.Series:
    """Return a Series with train/validation/test/None (row dropped) per row."""
    snap = data["snapshot_date"]
    day = lambda s: pd.Timestamp(s, tz="UTC")  # noqa: E731
    period = pd.Series(None, index=data.index, dtype="object")
    period[(snap <= day(plan.train_end)) & (data["label_end_utc"] < day(plan.val_start))] = "train"
    period[(snap >= day(plan.val_start)) & (snap <= day(plan.val_end))
           & (data["label_end_utc"] < day(plan.test_start))] = "validation"
    period[(snap >= day(plan.test_start)) & (snap <= day(plan.test_end))] = "test"
    if not plan.visitor_disjoint:
        return period
    bucket = _bucket(data["customer_id"].astype(str), plan.visitor_fractions, plan.seed)
    return period.where(period == bucket)


def split_frames(data: pd.DataFrame, plan: SplitPlan) -> dict[str, pd.DataFrame]:
    split = assign_split(data, plan)
    parts = {name: data.loc[split == name].reset_index(drop=True) for name in SPLITS}
    validate_split(parts, plan.visitor_disjoint)
    return parts


def validate_split(parts: dict[str, pd.DataFrame], visitor_disjoint: bool = True) -> None:
    """Hard checks mirroring the shared benchmark validator."""
    for name, p in parts.items():
        if p.empty or p["y"].nunique() < 2:
            raise ValueError(f"{name} split must contain both classes")
    ids = {k: set(v["customer_id"]) for k, v in parts.items()}
    for a, b in (("train", "validation"), ("train", "test"), ("validation", "test")):
        if visitor_disjoint and ids[a] & ids[b]:
            raise ValueError(f"customer_id appears in both {a} and {b}")
    for early, late in (("train", "validation"), ("validation", "test")):
        if parts[early]["label_end_utc"].max() >= parts[late]["snapshot_date"].min():
            raise ValueError(f"{early} labels overlap the {late} snapshot period")


def manifest(data: pd.DataFrame, parts: dict[str, pd.DataFrame], plan: SplitPlan,
             features: list[str], label_task: str) -> dict:
    assignment = pd.concat([p[["customer_id", "snapshot_date"]].assign(split=k) for k, p in parts.items()])
    assignment = assignment.sort_values(["customer_id", "snapshot_date"])
    digest = hashlib.sha256(assignment.to_csv(index=False).encode()).hexdigest()
    summary = {}
    for k, p in parts.items():
        summary[k] = {
            "rows": int(len(p)), "visitors": int(p["customer_id"].nunique()),
            "positives": int(p["y"].sum()), "prevalence": round(float(p["y"].mean()), 4),
            "snapshot_min": p["snapshot_date"].min().strftime("%Y-%m-%d"),
            "snapshot_max": p["snapshot_date"].max().strftime("%Y-%m-%d"),
            "label_end_max": p["label_end_utc"].max().strftime("%Y-%m-%d"),
        }
    used = sum(v["rows"] for v in summary.values())
    return {
        "split_version": plan.version, "plan": asdict(plan), "label_task": label_task,
        "features": features, "supervised_rows": int(len(data)), "rows_used": used,
        "rows_dropped_by_purge_or_bucket": int(len(data) - used),
        "splits": summary, "assignment_sha256": digest,
        "rules": [
            "time-ordered periods; test = last mature weeks",
            "strict purge: earlier label_end < next split's first snapshot",
            "visitor hashed into one bucket; bucket contributes only within its period"
            if plan.visitor_disjoint else "time-only sensitivity: visitors may repeat across splits",
        ],
    }


def export_benchmark_csv(parts: dict[str, pd.DataFrame], features: list[str], path) -> None:
    """modeling_snapshots.csv for research/baselines (decision_tree.py, gaussian_nb.py)."""
    rows = []
    for name, p in parts.items():
        out = pd.DataFrame({
            "customer_id": p["customer_id"].astype(str),
            "snapshot_date": p["snapshot_date"].dt.strftime("%Y-%m-%d"),
            "feature_end": pd.to_datetime(p["feature_max_event_time_utc"], utc=True).dt.strftime("%Y-%m-%d")
            if "feature_max_event_time_utc" in p else p["snapshot_date"].dt.strftime("%Y-%m-%d"),
            "label_end": p["label_end_utc"].dt.strftime("%Y-%m-%d"),
            "label_status": p["label_status"],
            "target_ghost": p["y"].astype(int).astype(str),
            "split": name,
        })
        from .data import to_matrix
        out = pd.concat([out, to_matrix(p, features).reset_index(drop=True)], axis=1)
        rows.append(out)
    pd.concat(rows, ignore_index=True).to_csv(path, index=False)
