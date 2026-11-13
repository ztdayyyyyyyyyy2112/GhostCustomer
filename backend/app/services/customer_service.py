from __future__ import annotations

import json
from hashlib import sha256
from typing import Any
from fastapi import HTTPException
from backend.app.config import settings
from backend.app.services.artifacts import load_json_artifact
from backend.app.schemas.api import (
    Customer,
    CustomerDetailResponse,
    CustomerStatus,
    CustomersResponse,
    CustomerWeekly,
    DateRange,
    OverviewResponse,
    SortField,
    SortOrder,
)


def _load_fixtures() -> dict[str, Any] | None:
    if settings.FIXTURES_PATH.exists():
        try:
            with open(settings.FIXTURES_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None
    return None


def get_overview_data() -> OverviewResponse:
    # 1. Check for real processed data artifacts
    processed_overview_file = settings.DATA_PROCESSED_DIR / "overview.json"
    overview = load_json_artifact(processed_overview_file, OverviewResponse, "Processed overview")
    if overview is not None:
        return overview

    # 2. Check for enabled demo fixtures
    if settings.ENABLE_DEMO_FIXTURES:
        fixtures = _load_fixtures()
        if fixtures and "overview" in fixtures:
            return OverviewResponse(**fixtures["overview"])

    # 3. Default empty state conforming to api_contract.md
    return OverviewResponse(
        total_customers=0,
        active_count=0,
        ghost_count=0,
        candidate_count=0,
        unknown_count=0,
        inactive_count=0,
        recovered_count=0,
        active_rate=None,
        ghost_rate=None,
        date_range=None,
        dataset_notice="Cohort unavailable until data processing pipeline runs",
    )


def _load_customers_pool() -> list[Customer]:
    processed_customers_file = settings.DATA_PROCESSED_DIR / "customers.json"
    if processed_customers_file.exists():
        try:
            with open(processed_customers_file, "r", encoding="utf-8") as f:
                raw_items = json.load(f)
                return [Customer(**item) for item in raw_items]
        except (OSError, ValueError, TypeError) as exc:
            raise HTTPException(status_code=503, detail="Processed customer artifact is invalid") from exc

    if settings.ENABLE_DEMO_FIXTURES:
        fixtures = _load_fixtures()
        if fixtures and "customers" in fixtures:
            return [Customer(**item) for item in fixtures["customers"]]

    return []


def _customers_notice() -> str:
    if (settings.DATA_PROCESSED_DIR / "customers.json").exists():
        return "DỮ LIỆU ĐÃ XỬ LÝ — kiểm tra nguồn, cohort và nhãn trong evidence register"
    if settings.ENABLE_DEMO_FIXTURES:
        return "DỮ LIỆU MOCK MINH HỌA — không phải kết quả nghiên cứu"
    return "Customer data unavailable until data processing pipeline runs"


def get_customers_data(
    page: int = 1,
    page_size: int = 20,
    status: CustomerStatus | None = None,
    search: str | None = None,
    sort: SortField = "snapshot_date",
    order: SortOrder = "desc",
) -> CustomersResponse:
    items = _load_customers_pool()

    if status:
        items = [item for item in items if item.status == status]

    if search:
        search_lower = search.strip().lower()
        items = [item for item in items if search_lower in item.customer_id.lower()]

    reverse = (order == "desc")
    non_null = [item for item in items if getattr(item, sort, None) is not None]
    null_items = [item for item in items if getattr(item, sort, None) is None]
    non_null.sort(key=lambda item: getattr(item, sort), reverse=reverse)
    sorted_items = non_null + null_items

    total = len(sorted_items)
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paged_items = sorted_items[start_idx:end_idx]

    return CustomersResponse(
        items=paged_items,
        page=page,
        page_size=page_size,
        total=total,
        dataset_notice=_customers_notice(),
    )


def get_customer_detail_data(
    customer_id: str, snapshot_date: str | None = None
) -> CustomerDetailResponse | None:
    items = _load_customers_pool()
    matches = [
        item for item in items
        if item.customer_id == customer_id
        and (snapshot_date is None or item.snapshot_date == snapshot_date)
    ]
    if not matches:
        return None
    customer = max(matches, key=lambda item: item.snapshot_date)

    processed = (settings.DATA_PROCESSED_DIR / "customers.json").exists()
    if processed:
        customer_hash = sha256(customer.customer_id.encode("utf-8")).hexdigest()
        detail_file = settings.DATA_PROCESSED_DIR / "customer_details" / customer.snapshot_date / f"{customer_hash}.json"
        if detail_file.exists():
            try:
                with detail_file.open("r", encoding="utf-8") as stream:
                    detail = CustomerDetailResponse(**json.load(stream))
            except (OSError, ValueError, TypeError) as exc:
                raise HTTPException(status_code=503, detail="Processed customer detail artifact is invalid") from exc
            if detail.customer != customer or detail.status != customer.status:
                raise HTTPException(status_code=503, detail="Processed customer detail does not match snapshot")
            return detail

    # The summary cannot establish a 4-week feature or a dated timeline by itself.
    weekly_timeline: list[CustomerWeekly] = []
    current_features: dict[str, float | int | None] = {} if processed else {
        "sessions_4w": customer.sessions,
        "views_4w": customer.views,
    }

    if settings.ENABLE_DEMO_FIXTURES and not processed:
        fixtures = _load_fixtures()
        if fixtures and customer.customer_id == "C001" and "weekly_timeline" in fixtures:
            weekly_timeline = [CustomerWeekly(**row) for row in fixtures["weekly_timeline"]]

    return CustomerDetailResponse(
        customer=customer,
        current_features=current_features,
        weekly_timeline=weekly_timeline,
        status=customer.status,
        dataset_notice=(
            "Processed snapshot summary; detailed features and timeline unavailable"
            if processed else _customers_notice()
        ),
    )
