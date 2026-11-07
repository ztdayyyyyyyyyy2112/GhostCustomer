from __future__ import annotations

from fastapi.testclient import TestClient


def test_health_endpoints(client: TestClient) -> None:
    root_res = client.get("/")
    assert root_res.status_code == 200
    assert root_res.json()["status"] == "ok"

    health_res = client.get("/health")
    assert health_res.status_code == 200
    assert health_res.json()["status"] == "healthy"


def test_cors_preflight(client: TestClient) -> None:
    res = client.options(
        "/api/overview",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert res.status_code == 200
    assert res.headers.get("access-control-allow-origin") == "http://localhost:3000"


def test_overview_default_empty_state(client: TestClient) -> None:
    res = client.get("/api/overview")
    assert res.status_code == 200
    data = res.json()
    assert data["total_customers"] == 0
    assert data["active_count"] == 0
    assert data["ghost_count"] == 0
    assert data["active_rate"] is None
    assert data["ghost_rate"] is None
    assert "Cohort unavailable until data processing pipeline runs" in data["dataset_notice"]


def test_overview_with_fixtures(demo_client: TestClient) -> None:
    res = demo_client.get("/api/overview")
    assert res.status_code == 200
    data = res.json()
    assert data["total_customers"] == 5
    assert data["active_count"] == 2
    assert data["ghost_count"] == 1
    assert data["active_rate"] == 0.4
    assert data["ghost_rate"] == 0.2
    assert data["date_range"] == {"start": "2026-01-05", "end": "2026-02-16"}


def test_customers_pagination_and_filtering(demo_client: TestClient) -> None:
    # All customers
    res = demo_client.get("/api/customers?page=1&page_size=2")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 5
    assert len(data["items"]) == 2
    assert data["page"] == 1
    assert data["page_size"] == 2

    # Status filter
    res_ghost = demo_client.get("/api/customers?status=ghost")
    assert res_ghost.status_code == 200
    ghost_data = res_ghost.json()
    assert ghost_data["total"] == 1
    assert ghost_data["items"][0]["customer_id"] == "C001"

    # Search filter
    res_search = demo_client.get("/api/customers?search=c003")
    assert res_search.status_code == 200
    search_data = res_search.json()
    assert search_data["total"] == 1
    assert search_data["items"][0]["customer_id"] == "C003"

    # Sorting
    res_sort = demo_client.get("/api/customers?sort=decay&order=desc")
    assert res_sort.status_code == 200
    sort_data = res_sort.json()
    decays = [item["decay"] for item in sort_data["items"] if item["decay"] is not None]
    assert decays == sorted(decays, reverse=True)


def test_customers_validation_error(client: TestClient) -> None:
    res = client.get("/api/customers?page=0")
    assert res.status_code == 422
    assert "detail" in res.json()

    res_large = client.get("/api/customers?page_size=200")
    assert res_large.status_code == 422


def test_customer_detail(demo_client: TestClient) -> None:
    res = demo_client.get("/api/customers/C001")
    assert res.status_code == 200
    data = res.json()
    assert data["customer"]["customer_id"] == "C001"
    assert data["status"] == "ghost"
    assert "sessions_4w" in data["current_features"]
    assert len(data["weekly_timeline"]) > 0

    res_404 = demo_client.get("/api/customers/UNKNOWN_999")
    assert res_404.status_code == 404
    assert "Không tìm thấy" in res_404.json()["detail"]


def test_statistics_endpoint(client: TestClient) -> None:
    res = client.get("/api/statistics")
    assert res.status_code == 200
    data = res.json()
    assert data["groups"] == []
    assert data["estimates"] == []
    assert data["tests"] == []
    assert "Results unavailable until statistical pipeline runs" in data["dataset_notice"]


def test_forecast_endpoint(client: TestClient) -> None:
    res = client.get("/api/forecast")
    assert res.status_code == 200
    data = res.json()
    assert data["history"] == []
    assert data["predictions"] == []
    assert data["method"] is None
    assert "Forecast unavailable until time-series analysis runs" in data["dataset_notice"]


def test_predict_endpoint_model_unavailable(client: TestClient) -> None:
    payload = {"customer_id": "C001", "snapshot_date": "2026-02-16"}
    res = client.post("/api/predict", json=payload)
    assert res.status_code == 503
    assert res.json()["detail"] == "Prediction model unavailable"


def test_predict_endpoint_with_fixtures(demo_client: TestClient) -> None:
    # Success case
    payload = {"customer_id": "C001", "snapshot_date": "2026-02-16"}
    res = demo_client.post("/api/predict", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["score"] == 0.73
    assert data["model_version"] == "mock-v0"

    # Mismatched snapshot
    bad_date = {"customer_id": "C001", "snapshot_date": "2025-01-01"}
    res_bad = demo_client.post("/api/predict", json=bad_date)
    assert res_bad.status_code == 422

    # Insufficient data (C005 has risk_score null)
    c5 = {"customer_id": "C005", "snapshot_date": "2026-02-16"}
    res_c5 = demo_client.post("/api/predict", json=c5)
    assert res_c5.status_code == 422

    # Unknown customer
    c_unknown = {"customer_id": "C999", "snapshot_date": "2026-02-16"}
    res_unknown = demo_client.post("/api/predict", json=c_unknown)
    assert res_unknown.status_code == 404

    # Missing fields
    res_empty = demo_client.post("/api/predict", json={})
    assert res_empty.status_code == 422


def test_model_metrics_endpoint(client: TestClient) -> None:
    res = client.get("/api/model/metrics")
    assert res.status_code == 200
    data = res.json()
    assert data["models"] == []
    assert data["evaluation_context"] is None
    assert "Metrics unavailable until held-out evaluation runs" in data["dataset_notice"]
