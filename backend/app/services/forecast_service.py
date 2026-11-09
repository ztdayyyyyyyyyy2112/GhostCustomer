from __future__ import annotations

import json
from typing import Any
from backend.app.config import settings
from backend.app.schemas.api import ForecastResponse
from backend.app.services.artifacts import load_json_artifact


def _load_fixtures() -> dict[str, Any] | None:
    if settings.FIXTURES_PATH.exists():
        try:
            with open(settings.FIXTURES_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None
    return None


def get_forecast_data() -> ForecastResponse:
    # 1. Check for real forecast artifact
    forecast_file = settings.RESEARCH_DIR / "forecasting" / "results.json"
    forecast = load_json_artifact(forecast_file, ForecastResponse, "Forecast")
    if forecast is not None:
        return forecast

    # 2. Check for demo fixtures if enabled
    if settings.ENABLE_DEMO_FIXTURES:
        fixtures = _load_fixtures()
        if fixtures and "forecast" in fixtures:
            return ForecastResponse(**fixtures["forecast"])

    # 3. Default empty state per docs/api_contract.md
    return ForecastResponse(
        history=[],
        fitted=[],
        predictions=[],
        lower_ci=[],
        upper_ci=[],
        method=None,
        mae=None,
        rmse=None,
        smape=None,
        train_end=None,
        unit=None,
        series_length=None,
        dataset_notice="Forecast unavailable until time-series analysis runs",
    )
