from __future__ import annotations

from pathlib import Path

import pandas as pd


RAW_COLUMNS = ["timestamp", "visitorid", "event", "itemid", "transactionid"]
EVENT_MAP = {"view": "view", "addtocart": "addtocart", "transaction": "transaction"}


def clean_events(raw_path: str | Path, extreme_visitor_quantile: float = 0.999) -> pd.DataFrame:
    raw = pd.read_csv(
        raw_path,
        dtype={"timestamp": "int64", "visitorid": "int64", "event": "string", "itemid": "int64", "transactionid": "Int64"},
        keep_default_na=True,
    )
    if list(raw.columns) != RAW_COLUMNS:
        raise ValueError(f"unexpected events.csv columns: {list(raw.columns)}")
    raw["source_row"] = pd.Series(range(2, len(raw) + 2), dtype="int64")
    raw["is_exact_duplicate"] = raw.duplicated(subset=RAW_COLUMNS, keep="first")
    event = raw["event"].str.strip().str.lower()
    mapped = event.map(EVENT_MAP)
    if mapped.isna().any():
        unknown = sorted(event[mapped.isna()].dropna().unique().tolist())
        raise ValueError(f"unknown event value(s): {unknown}")
    is_transaction = mapped.eq("transaction")
    if not is_transaction.equals(raw["transactionid"].notna()):
        raise ValueError("transactionid must be present only for transaction events")
    if raw["visitorid"].isna().any() or raw["itemid"].isna().any():
        raise ValueError("visitorid and itemid must not be null")

    event_counts = raw.groupby("visitorid", sort=False).size()
    extreme_cutoff = event_counts.quantile(extreme_visitor_quantile)
    extreme_visitors = event_counts.index[event_counts.gt(extreme_cutoff)]
    cleaned = pd.DataFrame(
        {
            "visitorid": raw["visitorid"].astype("int64"),
            "event_time_utc": pd.to_datetime(raw["timestamp"], unit="ms", utc=True, errors="raise"),
            "event_type": mapped.astype("category"),
            "itemid": raw["itemid"].astype("int64"),
            "transactionid": raw["transactionid"].astype("Int64"),
            "source_row": raw["source_row"],
            "is_exact_duplicate": raw["is_exact_duplicate"].astype(bool),
            "is_extreme_visitor": raw["visitorid"].isin(extreme_visitors),
        }
    )
    if len(cleaned) != len(raw) or cleaned["event_time_utc"].isna().any():
        raise AssertionError("cleaning changed row count or produced a null timestamp")
    return cleaned.sort_values(["visitorid", "event_time_utc", "source_row"], kind="mergesort").reset_index(drop=True)
