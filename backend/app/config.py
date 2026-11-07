from __future__ import annotations

import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings:
    API_TITLE: str = "GhostCustomer API"
    API_VERSION: str = "0.2.0"
    API_PREFIX: str = "/api"

    CORS_ORIGINS: list[str] = [
        origin.strip()
        for origin in os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")
        if origin.strip()
    ]

    DATA_PROCESSED_DIR: Path = PROJECT_ROOT / "data" / "processed"
    MODELS_DIR: Path = PROJECT_ROOT / "ai" / "models"
    RESEARCH_DIR: Path = PROJECT_ROOT / "research"
    FIXTURES_PATH: Path = PROJECT_ROOT / "frontend" / "src" / "mocks" / "data.json"

    # When ENABLE_DEMO_FIXTURES is true, endpoints will serve the contract fixture data
    # (explicitly tagged as illustrative demo data) when processed research artifacts are absent.
    # Default is False so production/research mode returns strict empty states / 503.
    ENABLE_DEMO_FIXTURES: bool = os.getenv("ENABLE_DEMO_FIXTURES", "0") in ("1", "true", "True")


settings = Settings()
