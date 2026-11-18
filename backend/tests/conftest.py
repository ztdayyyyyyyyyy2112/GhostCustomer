from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from backend.app.config import settings
from backend.app.main import app


@pytest.fixture
def isolated_artifacts(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    monkeypatch.setattr(settings, "DATA_PROCESSED_DIR", tmp_path / "processed")
    monkeypatch.setattr(settings, "RESEARCH_DIR", tmp_path / "research")
    # Keep tests independent of a locally trained model or ai/evaluation outputs.
    monkeypatch.setattr(settings, "MODELS_DIR", tmp_path / "ai" / "models")


@pytest.fixture
def client(isolated_artifacts: None) -> TestClient:
    return TestClient(app)


@pytest.fixture
def demo_client(monkeypatch: pytest.MonkeyPatch, isolated_artifacts: None) -> TestClient:
    monkeypatch.setattr(settings, "ENABLE_DEMO_FIXTURES", True)
    return TestClient(app)
