from __future__ import annotations

import json
from typing import Any
from backend.app.config import settings
from backend.app.schemas.api import StatisticsResponse
from backend.app.services.artifacts import load_json_artifact


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
    stats = load_json_artifact(stats_file, StatisticsResponse, "Statistics")
    if stats is not None:
        return stats

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
