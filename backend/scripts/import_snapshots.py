"""Convert a processed summary CSV/Parquet to the existing customers.json contract."""
import argparse
from datetime import date
from hashlib import sha256
import json
from math import isfinite
from pathlib import Path
from tempfile import NamedTemporaryFile

import pandas as pd
from backend.app.schemas.api import Customer


def export(source: Path, output: Path):
    source = Path(source)
    output = Path(output)
    if source.resolve() == output.resolve():
        raise ValueError("Input and output must differ")
    if source.suffix == ".csv":
        frame = pd.read_csv(source, dtype={"visitorid": "string", "customer_id": "string"})
    elif source.suffix == ".parquet":
        frame = pd.read_parquet(source)
    else:
        raise ValueError("Expected CSV or Parquet")
    if "visitorid" in frame and "customer_id" not in frame:
        frame = frame.rename(columns={"visitorid": "customer_id"})
    required = {"customer_id", "snapshot_date", "status"}
    if not required <= set(frame.columns):
        raise ValueError(f"Missing columns {sorted(required - set(frame.columns))}")
    if "feature_max_event_time" in frame:
        available = pd.to_datetime(frame.feature_max_event_time, utc=True, errors="raise")
        snapshots = pd.to_datetime(frame.snapshot_date, utc=True, errors="raise")
        if available.isna().any() or snapshots.isna().any() or (available > snapshots).any():
            raise ValueError("Missing feature timestamps or post-snapshot leakage")
    rows, seen = [], set()
    columns = [key for key in Customer.model_fields if key in frame]
    for row in frame[columns].astype(object).where(frame[columns].notna(), None).to_dict("records"):
        visitor = row["customer_id"]
        if not isinstance(visitor, str) or not visitor.strip():
            raise ValueError("Customer identifiers must be nonempty strings")
        day = row["snapshot_date"]
        if not isinstance(day, str) or date.fromisoformat(day).isoformat() != day:
            raise ValueError("Use canonical YYYY-MM-DD snapshots")
        key = (visitor, day)
        if key in seen:
            raise ValueError(f"Duplicate snapshot {key}")
        seen.add(key)
        customer = Customer.model_validate(row)
        for key in ("sessions", "views", "decay", "risk_score"):
            value = getattr(customer, key)
            if value is not None and not isfinite(value):
                raise ValueError(f"Nonfinite {key}")
        if any(value is not None and value < 0 for value in (customer.sessions, customer.views)):
            raise ValueError("Negative count")
        if customer.risk_score is not None and not 0 <= customer.risk_score <= 1:
            raise ValueError("Risk score outside [0, 1]")
        rows.append(customer.model_dump())
    digest = sha256(source.read_bytes()).hexdigest()
    output.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(dir=output.parent, delete=False, mode="w", encoding="utf-8") as stream:
        temporary = Path(stream.name)
        try:
            json.dump(rows, stream, allow_nan=False, ensure_ascii=False)
        except BaseException:
            stream.close()
            temporary.unlink()
            raise
    try:
        temporary.replace(output)
    finally:
        temporary.unlink(missing_ok=True)
    return {"snapshots": len(rows), "input_sha256": digest, "source_dtypes": {name: str(dtype) for name, dtype in frame.dtypes.items()}, "feature_cutoff_checked": "feature_max_event_time" in frame}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    print(json.dumps(export(args.input, args.output)))
