from __future__ import annotations

import json
import math
from pathlib import Path
from typing import TypeVar

from fastapi import HTTPException
from pydantic import BaseModel


T = TypeVar("T", bound=BaseModel)


def _check_numbers(value: object) -> None:
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("Artifact contains a nonfinite number")
    if isinstance(value, dict):
        for item in value.values():
            _check_numbers(item)
    elif isinstance(value, list):
        for item in value:
            _check_numbers(item)


def load_json_artifact(path: Path, model: type[T], label: str) -> T | None:
    if not path.exists():
        return None
    try:
        with path.open("r", encoding="utf-8") as stream:
            payload = json.load(stream)
            _check_numbers(payload)
            result = model.model_validate(payload)
            _check_numbers(result.model_dump())
            return result
    except (OSError, ValueError, TypeError) as exc:
        raise HTTPException(status_code=503, detail=f"{label} artifact is invalid") from exc
