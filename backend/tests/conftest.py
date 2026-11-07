from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from backend.app.config import settings
from backend.app.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def demo_client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setattr(settings, "ENABLE_DEMO_FIXTURES", True)
    return TestClient(app)
