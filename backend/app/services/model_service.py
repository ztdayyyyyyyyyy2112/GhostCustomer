from __future__ import annotations

import json
from importlib import import_module
from typing import Any
from fastapi import HTTPException
from pydantic import ValidationError
from backend.app.config import settings
from backend.app.services.artifacts import load_json_artifact
from backend.app.schemas.api import (
    ModelMetricsResponse,
    PredictRequest,
    PredictResponse,
)
from backend.app.services.customer_service import _load_customers_pool


def _load_fixtures() -> dict[str, Any] | None:
    if settings.FIXTURES_PATH.exists():
        try:
            with open(settings.FIXTURES_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None
    return None


def _run_real_predict(request: PredictRequest) -> PredictResponse | None:
    runtime_path = settings.MODELS_DIR.parent / "inference" / "runtime.py"
    if not runtime_path.exists():
        return None
    try:
        runtime = import_module("ai.inference.runtime")
        prediction = runtime.predict(request.model_dump(exclude_none=True))
        return PredictResponse.model_validate(prediction)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        if isinstance(exc, ValidationError):
            raise HTTPException(status_code=503, detail="Model response does not match API contract") from exc
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Prediction model unavailable") from exc


def run_predict(request: PredictRequest) -> PredictResponse:
    real_prediction = _run_real_predict(request)
    if real_prediction is not None:
        return real_prediction

    # If in demo fixture mode (or mock demonstration):
    if settings.ENABLE_DEMO_FIXTURES:
        fixtures = _load_fixtures() or {}
        default_prediction = fixtures.get("prediction", {})

        if request.customer_id is not None:
            customers = _load_customers_pool()
            customer = next((c for c in customers if c.customer_id == request.customer_id), None)
            if not customer:
                raise HTTPException(status_code=404, detail=f"Không tìm thấy khách hàng {request.customer_id}")
            if request.snapshot_date != customer.snapshot_date:
                raise HTTPException(status_code=422, detail="Snapshot không khớp với dữ liệu mock.")
            if customer.risk_score is None:
                raise HTTPException(status_code=422, detail="Khách hàng này chưa đủ dữ liệu để dự đoán.")

            return PredictResponse(
                score=customer.risk_score,
                risk_label="mock",
                top_factors=[],
                model_version=default_prediction.get("model_version", "mock-v0"),
                dataset_notice="DỰ ĐOÁN MOCK MINH HỌA — không phải kết quả mô hình",
            )
        elif request.features:
            # Score synthetic feature payload for contract verification
            return PredictResponse(
                score=0.5,
                risk_label="mock",
                top_factors=[],
                model_version=default_prediction.get("model_version", "mock-v0"),
                dataset_notice="DỰ ĐOÁN MOCK MINH HỌA — không phải kết quả mô hình",
            )

    # No installed inference runtime or illustrative fixture.
    raise HTTPException(status_code=503, detail="Prediction model unavailable")


def get_model_metrics_data() -> ModelMetricsResponse:
    # 1. Check for real evaluation metrics artifact
    metrics_file = settings.MODELS_DIR.parent / "evaluation" / "metrics.json"
    metrics = load_json_artifact(metrics_file, ModelMetricsResponse, "Model metrics")
    if metrics is not None:
        return metrics

    # 2. Check for demo fixtures if enabled
    if settings.ENABLE_DEMO_FIXTURES:
        fixtures = _load_fixtures()
        if fixtures and "metrics" in fixtures:
            return ModelMetricsResponse(**fixtures["metrics"])

    # 3. Default empty state per docs/api_contract.md
    return ModelMetricsResponse(
        models=[],
        comparison=[],
        evaluation_context=None,
        confusion_matrix=None,
        calibration=[],
        dataset_notice="Metrics unavailable until held-out evaluation runs",
    )
