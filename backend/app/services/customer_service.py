from __future__ import annotations

import json
from typing import Any
from backend.app.config import settings
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
    if processed_overview_file.exists():
        try:
            with open(processed_overview_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return OverviewResponse(**data)
        except Exception:
            pass

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
        except Exception:
            pass

    if settings.ENABLE_DEMO_FIXTURES:
        fixtures = _load_fixtures()
        if fixtures and "customers" in fixtures:
            return [Customer(**item) for item in fixtures["customers"]]

    return []


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
    )


def get_customer_detail_data(customer_id: str) -> CustomerDetailResponse | None:
    items = _load_customers_pool()
    customer = next((c for c in items if c.customer_id == customer_id), None)
    if not customer:
        return None

    # Load weekly timeline if available
    weekly_timeline: list[CustomerWeekly] = []
    current_features: dict[str, float | int | None] = {
        "sessions_4w": customer.sessions,
        "views_4w": customer.views,
    }

    if settings.ENABLE_DEMO_FIXTURES:
        fixtures = _load_fixtures()
        if fixtures and customer.customer_id == "C001" and "weekly_timeline" in fixtures:
            weekly_timeline = [CustomerWeekly(**row) for row in fixtures["weekly_timeline"]]

    return CustomerDetailResponse(
        customer=customer,
        current_features=current_features,
        weekly_timeline=weekly_timeline,
        status=customer.status,
    )
