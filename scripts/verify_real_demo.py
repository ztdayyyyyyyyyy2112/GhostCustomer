"""Fail-fast check of the complete local real-data defense demo."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from fastapi.testclient import TestClient

from backend.app.config import settings
from backend.app.main import app


ROOT = Path(__file__).resolve().parents[1]


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def check_response(client: TestClient, path: str) -> dict:
    response = client.get(path)
    assert response.status_code == 200, f"{path}: HTTP {response.status_code}: {response.text[:200]}"
    result = response.json()
    assert "mock" not in result.get("dataset_notice", "").lower(), f"{path}: mock response"
    return result


def run() -> dict:
    settings.ENABLE_DEMO_FIXTURES = False
    model_meta = json.loads((ROOT / "ai/evaluation/model_meta.json").read_text(encoding="utf-8"))
    summary = json.loads((ROOT / "ai/evaluation/run_summary.json").read_text(encoding="utf-8"))
    model_path = ROOT / "ai/models/ghost_model.joblib"
    feature_path = ROOT / "data/processed/customer_features.parquet"
    label_path = ROOT / "data/processed/customer_labels.parquet"
    assert sha(model_path) == model_meta["sha256"], "Saved model SHA-256 differs from model metadata"
    assert sha(feature_path) == summary["inputs"]["features_sha256"], "Features differ from model run"
    assert sha(label_path) == summary["inputs"]["labels_sha256"], "Labels differ from model run"
    with TestClient(app) as client:
        overview = check_response(client, "/api/overview")
        assert overview["total_customers"] > 0
        customers = check_response(client, "/api/customers?page_size=1&status=ghost")
        assert customers["total"] > 0 and len(customers["items"]) == 1
        customer = customers["items"][0]
        detail = check_response(client, f"/api/customers/{customer['customer_id']}?snapshot_date={customer['snapshot_date']}")
        assert detail["customer"] == customer and detail["weekly_timeline"]
        statistics = check_response(client, "/api/statistics")
        assert statistics["groups"] and statistics["tests"] and statistics["estimates"]
        forecast = check_response(client, "/api/forecast")
        assert forecast["history"] and forecast["predictions"] and forecast["mae"] is not None
        metrics = check_response(client, "/api/model/metrics")
        assert metrics["models"] and metrics["evaluation_context"]["model_version"] == model_meta["model_version"]
        response = client.post("/api/predict", json={"customer_id": customer["customer_id"], "snapshot_date": customer["snapshot_date"]})
        assert response.status_code == 200, f"predict: HTTP {response.status_code}: {response.text[:200]}"
        prediction = response.json()
        assert prediction["model_version"] == model_meta["model_version"]
        assert 0 <= prediction["score"] <= 1 and prediction["risk_label"] != "mock"
        unknown = client.post("/api/predict", json={"customer_id": "unknown-defense-smoke", "snapshot_date": customer["snapshot_date"]})
        assert unknown.status_code == 404, f"unknown customer: HTTP {unknown.status_code}"
        invalid = client.post("/api/predict", json={"customer_id": customer["customer_id"], "snapshot_date": "not-a-date"})
        assert invalid.status_code == 422, f"invalid date: HTTP {invalid.status_code}"
    return {
        "data_mode": "real", "api_endpoints_checked": 7,
        "customer_snapshots": overview["total_customers"], "statistics_tests": len(statistics["tests"]),
        "forecast_history_weeks": len(forecast["history"]), "forecast_future_weeks": len(forecast["predictions"]),
        "forecast_method": forecast["method"], "model_version": model_meta["model_version"],
        "model_sha256": model_meta["sha256"], "predict_404": unknown.status_code,
        "predict_422": invalid.status_code,
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
