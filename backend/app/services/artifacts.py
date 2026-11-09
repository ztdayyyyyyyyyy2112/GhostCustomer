from __future__ import annotations

import json
from pathlib import Path
from typing import TypeVar

from fastapi import HTTPException
from pydantic import BaseModel


T = TypeVar("T", bound=BaseModel)


def load_json_artifact(path: Path, model: type[T], label: str) -> T | None:
    if not path.exists():
        return None
    try:
        with path.open("r", encoding="utf-8") as stream:
            return model.model_validate(json.load(stream))
    except (OSError, ValueError, TypeError) as exc:
        raise HTTPException(status_code=503, detail=f"{label} artifact is invalid") from exc
