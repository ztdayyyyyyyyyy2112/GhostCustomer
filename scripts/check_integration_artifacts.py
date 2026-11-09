"""Read-only structural check for the research artifacts consumed by the API."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import date
from pathlib import Path

from pydantic import ValidationError


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.app.schemas.api import (  # noqa: E402
    Customer,
    CustomerDetailResponse,
    ForecastResponse,
    ModelMetricsResponse,
    OverviewResponse,
    StatisticsResponse,
)


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as stream:
        return json.load(stream)


def valid_iso_date(value: str) -> bool:
    try:
        return date.fromisoformat(value).isoformat() == value
    except ValueError:
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--require-complete",
        action="store_true",
        help="Fail when any handoff artifact or customer detail is missing.",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=ROOT,
        help="Project root to inspect (defaults to this script's repository).",
    )
    args = parser.parse_args()
    root = args.root.resolve()

    failures: list[str] = []
    missing: list[str] = []
    checked: list[str] = []

    artifacts = [
        ("overview", root / "data/processed/overview.json", OverviewResponse),
        ("statistics", root / "research/statistics/results.json", StatisticsResponse),
        ("forecast", root / "research/forecasting/results.json", ForecastResponse),
        ("model metrics", root / "ai/evaluation/metrics.json", ModelMetricsResponse),
    ]

    for label, path, schema in artifacts:
        if not path.is_file():
            missing.append(str(path.relative_to(root)))
            continue
        try:
            payload = schema.model_validate(load_json(path))
            if "mock" in payload.dataset_notice.casefold():
                raise ValueError("research artifact still says mock")
            if isinstance(payload, OverviewResponse):
                total = sum(
                    getattr(payload, field)
                    for field in (
                        "active_count", "ghost_count", "candidate_count",
                        "unknown_count", "inactive_count", "recovered_count",
                    )
                )
                if total != payload.total_customers:
                    raise ValueError("status counts do not sum to total_customers")
                for rate, count in (
                    (payload.active_rate, payload.active_count),
                    (payload.ghost_rate, payload.ghost_count),
                ):
                    expected = count / payload.total_customers if payload.total_customers else None
                    if (rate is None) != (expected is None) or (
                        rate is not None and expected is not None and abs(rate - expected) > 1e-6
                    ):
                        raise ValueError("active/ghost rates do not match cohort counts")
            if isinstance(payload, ForecastResponse):
                for series in (
                    payload.history, payload.fitted or [], payload.predictions,
                    payload.lower_ci, payload.upper_ci,
                ):
                    for point in series:
                        if not valid_iso_date(point.date) or not 0 <= point.value <= 1:
                            raise ValueError("forecast has an invalid date or rate")
            if isinstance(payload, ModelMetricsResponse):
                for row in payload.models:
                    if row.support < 0 or any(
                        value is not None and not 0 <= value <= 1
                        for value in (
                            row.prevalence, row.threshold, row.precision, row.recall,
                            row.f1, row.roc_auc, row.pr_auc, row.brier,
                        )
                    ):
                        raise ValueError("model metrics contain an invalid count or rate")
                matrix = payload.confusion_matrix
                if matrix is not None and (
                    len(matrix) != 2 or any(len(row) != 2 or any(value < 0 for value in row) for row in matrix)
                ):
                    raise ValueError("confusion_matrix must be a non-negative 2x2 array")
            checked.append(str(path.relative_to(root)))
        except (OSError, ValueError, TypeError, ValidationError) as exc:
            failures.append(f"{label}: {exc}")

    customers_path = root / "data/processed/customers.json"
    if not customers_path.is_file():
        missing.append(str(customers_path.relative_to(root)))
    else:
        try:
            raw_customers = load_json(customers_path)
            if not isinstance(raw_customers, list):
                raise ValueError("expected a JSON array")
            customers = [Customer.model_validate(row) for row in raw_customers]
            pairs = {(row.customer_id, row.snapshot_date) for row in customers}
            if len(pairs) != len(customers):
                raise ValueError("duplicate (customer_id, snapshot_date) rows")
            if any(not valid_iso_date(row.snapshot_date) for row in customers):
                raise ValueError("snapshot_date must be an ISO date (YYYY-MM-DD)")
            if any(
                (row.sessions is not None and row.sessions < 0)
                or (row.views is not None and row.views < 0)
                or (row.risk_score is not None and not 0 <= row.risk_score <= 1)
                for row in customers
            ):
                raise ValueError("customer counts or risk_score are outside their valid ranges")
            checked.append(f"{customers_path.relative_to(root)} ({len(customers)} snapshots)")

            missing_details = 0
            checked_details = 0
            for row in customers:
                digest = hashlib.sha256(row.customer_id.encode("utf-8")).hexdigest()
                path = root / "data/processed/customer_details" / row.snapshot_date / f"{digest}.json"
                if not path.is_file():
                    missing_details += 1
                    continue
                try:
                    detail = CustomerDetailResponse.model_validate(load_json(path))
                    if detail.customer != row or detail.status != row.status:
                        raise ValueError("detail does not match its customer snapshot")
                    if "mock" in detail.dataset_notice.casefold():
                        raise ValueError("detail still says mock")
                    checked_details += 1
                except (OSError, ValueError, TypeError, ValidationError) as exc:
                    failures.append(f"{path.relative_to(root)}: {exc}")
            checked.append(f"customer detail files: {checked_details}")
            if missing_details:
                missing.append(f"customer detail files: {missing_details} of {len(customers)}")
        except (OSError, ValueError, TypeError, ValidationError) as exc:
            failures.append(f"customers: {exc}")

    runtime_path = root / "ai/inference/runtime.py"
    if runtime_path.is_file():
        checked.append(str(runtime_path.relative_to(root)))
    else:
        missing.append(str(runtime_path.relative_to(root)))

    for item in checked:
        print(f"OK      {item}")
    for item in missing:
        print(f"MISSING {item}")
    for item in failures:
        print(f"INVALID {item}")
    print(f"Checked: {len(checked)}; missing: {len(missing)}; invalid: {len(failures)}")
    return 1 if failures or (args.require_complete and missing) else 0


if __name__ == "__main__":
    raise SystemExit(main())
