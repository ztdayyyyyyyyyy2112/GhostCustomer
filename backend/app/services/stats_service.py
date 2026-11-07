from __future__ import annotations

import json
from typing import Any
from backend.app.config import settings
from backend.app.schemas.api import StatisticsResponse


def _load_fixtures() -> dict[str, Any] | None:
    if settings.FIXTURES_PATH.exists():
        try:
            with open(settings.FIXTURES_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None
    return None


def get_statistics_data() -> StatisticsResponse:
    # 1. Check for real statistical results file
    stats_file = settings.RESEARCH_DIR / "statistics" / "results.json"
    if stats_file.exists():
        try:
            with open(stats_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return StatisticsResponse(**data)
        except Exception:
            pass

    # 2. Check for demo fixtures if enabled
    if settings.ENABLE_DEMO_FIXTURES:
        fixtures = _load_fixtures()
        if fixtures and "statistics" in fixtures:
            return StatisticsResponse(**fixtures["statistics"])

    # 3. Default empty state per docs/api_contract.md
    return StatisticsResponse(
        groups=[],
        estimates=[],
        tests=[],
        p_values=[],
        cis=[],
        assumptions=[],
        dataset_notice="Results unavailable until statistical pipeline runs",
    )
