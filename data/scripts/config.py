from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "data/config/pipeline.json"
EXPECTED_SHA256 = "3745aa83238b1e6d44d8fda209807899f420084398f94ddf745f3cbcfecbf9e7"


def load_config(path: str | Path = CONFIG_PATH) -> dict:
    config = json.loads(Path(path).read_text(encoding="utf-8"))
    if config["source"]["sha256"] != EXPECTED_SHA256:
        raise ValueError("configured Retailrocket hash differs from the audited source")
    if config["time"]["feature_interval"] != "[window_start,T)":
        raise ValueError("features must use a half-open pre-T interval")
    return config


DEFAULT_CONFIG = load_config()
FEATURE_COLUMNS = tuple(DEFAULT_CONFIG["feature_columns"])


def verify_source(path: str | Path, expected_sha256: str = EXPECTED_SHA256) -> dict:
    source = Path(path)
    digest = hashlib.sha256()
    with source.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    actual = digest.hexdigest()
    if actual != expected_sha256:
        raise ValueError(f"events.csv SHA-256 mismatch: expected {expected_sha256}, got {actual}")
    with source.open("r", encoding="utf-8", newline="") as stream:
        reader = csv.reader(stream)
        header = next(reader, None)
        if header != ["timestamp", "visitorid", "event", "itemid", "transactionid"]:
            raise ValueError(f"unexpected Retailrocket events.csv header: {header}")
        rows = sum(1 for _ in reader)
    result = {"path": str(source), "sha256": actual, "bytes": source.stat().st_size, "rows": rows}
    if result["bytes"] != DEFAULT_CONFIG["source"]["bytes"] or rows != DEFAULT_CONFIG["source"]["rows"]:
        raise ValueError(f"events.csv size/row count differs from E-00: {result}")
    return result
