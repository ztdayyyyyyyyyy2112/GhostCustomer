"""Generate accepted /api/predict response examples for E-08 (run where the model lives).

    python -m ai.inference.examples                   # writes docs/predict_examples.json

Calls the same `runtime.predict` the backend uses and records one success,
one unknown customer (404) and one invalid request (422) with the exact
model version, so Long and Thành can compare live API responses with it.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from . import runtime

OUT = Path(__file__).resolve().parents[2] / "docs" / "predict_examples.json"


def _call(payload):
    try:
        return {"request": payload, "status": 200, "response": runtime.predict(payload)}
    except LookupError as exc:
        return {"request": payload, "status": 404, "response": {"detail": str(exc)}}
    except ValueError as exc:
        return {"request": payload, "status": 422, "response": {"detail": str(exc)}}


def main() -> None:
    art = runtime.load_artifact()
    table = runtime._feature_table()
    scenario = art.get("scenario_id")
    if scenario and "scenario_id" in table:
        table = table[table["scenario_id"].astype(str) == str(scenario)]
    # latest snapshot of the first visitor at the test period start, for a realistic example
    latest = table["_snapshot"].max()
    row = table[table["_snapshot"] == latest].sort_values("customer_id").iloc[0]
    examples = [
        _call({"customer_id": str(row.customer_id), "snapshot_date": latest}),
        _call({"customer_id": "does-not-exist", "snapshot_date": latest}),
        _call({"customer_id": str(row.customer_id), "snapshot_date": "2015-02-30"}),
    ]
    doc = {"model_version": art["model_version"], "split_version": art.get("split_version"),
           "scenario_id": scenario, "generated_utc": pd.Timestamp.now(tz="UTC").isoformat(),
           "examples": examples}
    OUT.write_text(json.dumps(doc, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(doc, indent=2, ensure_ascii=False))
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
