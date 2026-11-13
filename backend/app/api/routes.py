from __future__ import annotations

from datetime import date

from fastapi import APIRouter, HTTPException, Query
from backend.app.schemas.api import (
    CustomerDetailResponse,
    CustomerStatus,
    CustomersResponse,
    ErrorResponse,
    ForecastResponse,
    ModelMetricsResponse,
    OverviewResponse,
    PredictRequest,
    PredictResponse,
    SortField,
    SortOrder,
    StatisticsResponse,
)
from backend.app.services.customer_service import (
    get_customer_detail_data,
    get_customers_data,
    get_overview_data,
)
from backend.app.services.forecast_service import get_forecast_data
from backend.app.services.model_service import get_model_metrics_data, run_predict
from backend.app.services.stats_service import get_statistics_data


router = APIRouter()


@router.get(
    "/overview",
    response_model=OverviewResponse,
    summary="Get cohort overview metrics",
)
def get_overview() -> OverviewResponse:
    return get_overview_data()


@router.get(
    "/customers",
    response_model=CustomersResponse,
    summary="Search, filter, and paginate customers",
)
def get_customers(
    page: int = Query(1, ge=1, description="One-based page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page (1-100)"),
    status: CustomerStatus | None = Query(None, description="Filter by operational status"),
    search: str | None = Query(None, description="Search by customer ID"),
    sort: SortField = Query("snapshot_date", description="Field to sort by"),
    order: SortOrder = Query("desc", description="Sort direction"),
) -> CustomersResponse:
    return get_customers_data(
        page=page,
        page_size=page_size,
        status=status,
        search=search,
        sort=sort,
        order=order,
    )


@router.get(
    "/customers/{id}",
    response_model=CustomerDetailResponse,
    responses={404: {"model": ErrorResponse, "description": "Customer not found"}},
    summary="Get detailed history and pre-T features for a customer",
)
def get_customer(
    id: str,
    snapshot_date: date | None = Query(None, description="ISO date of the selected visitor snapshot"),
) -> CustomerDetailResponse:
    detail = get_customer_detail_data(id, snapshot_date.isoformat() if snapshot_date else None)
    if not detail:
        raise HTTPException(status_code=404, detail=f"Không tìm thấy khách hàng {id}")
    return detail


@router.get(
    "/statistics",
    response_model=StatisticsResponse,
    summary="Get statistical test outputs, estimates, and group distributions",
)
def get_statistics() -> StatisticsResponse:
    return get_statistics_data()


@router.get(
    "/forecast",
    response_model=ForecastResponse,
    summary="Get time-series forecast and intervals",
)
def get_forecast() -> ForecastResponse:
    return get_forecast_data()


@router.post(
    "/predict",
    response_model=PredictResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Customer not found"},
        422: {"model": ErrorResponse, "description": "Validation or missing horizon error"},
        503: {"model": ErrorResponse, "description": "Model unavailable"},
    },
    summary="Run disengagement risk inference for a customer or feature vector",
)
def predict(request: PredictRequest) -> PredictResponse:
    return run_predict(request)


@router.get(
    "/model/metrics",
    response_model=ModelMetricsResponse,
    summary="Get held-out model evaluation, confusion matrix, and calibration",
)
def get_model_metrics() -> ModelMetricsResponse:
    return get_model_metrics_data()
