import csv
from pathlib import Path

import pytest

from data.scripts.config import FEATURE_COLUMNS, load_config, verify_source


ROOT = Path(__file__).resolve().parents[3]


def test_config_pins_expected_raw_hash():
    config = load_config(ROOT / "data/config/pipeline.json")
    assert config["source"]["sha256"] == "3745aa83238b1e6d44d8fda209807899f420084398f94ddf745f3cbcfecbf9e7"
    assert config["source"]["bytes"] == 94_237_913
    assert config["source"]["rows"] == 2_756_101


def test_source_verifier_rejects_a_hash_mismatch(tmp_path):
    source = tmp_path / "events.csv"
    source.write_text("timestamp,visitorid,event,itemid,transactionid\n1,1,view,2,\n", encoding="utf-8")
    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        verify_source(source)


def test_mock_rows_are_synthetic_and_match_feature_header():
    path = ROOT / "data/mock/customer_features_sample.csv"
    with path.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        rows = list(reader)
    assert reader.fieldnames == [*FEATURE_COLUMNS, "is_synthetic"]
    assert 10 <= len(rows) <= 30
    assert all(row["is_synthetic"] == "true" for row in rows)
    assert all(row["customer_id"].startswith("SYN-") for row in rows)
