from __future__ import annotations

from typing import Any, Literal
from pydantic import BaseModel, Field, model_validator


CustomerStatus = Literal["active", "ghost", "candidate", "recovered", "inactive", "unknown"]
TimelinePhase = Literal["baseline", "observation", "confirmation"]
ForecastUnit = Literal["day", "week"]
SortField = Literal["snapshot_date", "sessions", "views", "decay", "risk_score"]
SortOrder = Literal["asc", "desc"]


class DateRange(BaseModel):
    start: str
    end: str


class Customer(BaseModel):
    customer_id: str
    snapshot_date: str
    status: CustomerStatus
    sessions: int | None = None
    views: int | None = None
    decay: float | None = None
    risk_score: float | None = None


class CustomerWeekly(BaseModel):
    week_start: str
    views: int
    carts: int
    purchases: int
    sessions: int
    active_days: int
    phase: TimelinePhase


class OverviewResponse(BaseModel):
    total_customers: int
    active_count: int
    ghost_count: int
    candidate_count: int
    unknown_count: int
    inactive_count: int
    recovered_count: int
    active_rate: float | None = None
    ghost_rate: float | None = None
    date_range: DateRange | None = None
    dataset_notice: str


class CustomersResponse(BaseModel):
    items: list[Customer]
    page: int
    page_size: int
    total: int


class CustomerDetailResponse(BaseModel):
    customer: Customer
    current_features: dict[str, float | int | None]
    weekly_timeline: list[CustomerWeekly]
    status: CustomerStatus


class StatsResult(BaseModel):
    name: str
    hypothesis: str
    n: int
    statistic: float | None = None
    p_value: float | None = None
    effect_size: float | None = None
    ci_low: float | None = None
    ci_high: float | None = None
    method: str
    assumptions: list[str] = Field(default_factory=list)


class HistogramBin(BaseModel):
    lower: float
    upper: float
    count: int


class StatisticGroup(BaseModel):
    name: str
    metric: str
    unit: str
    n: int
    mean: float | None = None
    median: float | None = None
    q1: float | None = None
    q3: float | None = None
    min: float | None = None
    max: float | None = None
    histogram: list[HistogramBin] = Field(default_factory=list)


class StatisticEstimate(BaseModel):
    name: str
    n: int
    estimate: float
    ci_low: float | None = None
    ci_high: float | None = None
    method: str
    unit: str


class StatisticsResponse(BaseModel):
    groups: list[StatisticGroup] = Field(default_factory=list)
    estimates: list[StatisticEstimate] = Field(default_factory=list)
    tests: list[StatsResult] = Field(default_factory=list)
    p_values: list[float] = Field(default_factory=list)
    cis: list[Any] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    dataset_notice: str


class SeriesPoint(BaseModel):
    date: str
    value: float


class ForecastResponse(BaseModel):
    history: list[SeriesPoint] = Field(default_factory=list)
    fitted: list[SeriesPoint] | None = None
    predictions: list[SeriesPoint] = Field(default_factory=list)
    lower_ci: list[SeriesPoint] = Field(default_factory=list)
    upper_ci: list[SeriesPoint] = Field(default_factory=list)
    method: str | None = None
    mae: float | None = None
    rmse: float | None = None
    smape: float | None = None
    train_end: str | None = None
    unit: ForecastUnit | None = None
    series_length: int | None = None
    dataset_notice: str


class PredictRequest(BaseModel):
    customer_id: str | None = None
    snapshot_date: str | None = None
    features: dict[str, float | int | None] | None = None

    @model_validator(mode="after")
    def validate_request_shape(self) -> PredictRequest:
        has_id = bool(self.customer_id and self.snapshot_date)
        has_features = self.features is not None
        if not (has_id or has_features):
            raise ValueError("Request must provide either 'customer_id' with 'snapshot_date', or a 'features' dictionary.")
        return self


class FeatureContribution(BaseModel):
    feature: str
    contribution: float


class PredictResponse(BaseModel):
    score: float
    risk_label: str
    top_factors: list[FeatureContribution] = Field(default_factory=list)
    model_version: str
    dataset_notice: str


class ModelMetricRow(BaseModel):
    name: str
    model_version: str
    split: str
    support: int
    prevalence: float
    threshold: float | None = None
    precision: float | None = None
    recall: float | None = None
    f1: float | None = None
    roc_auc: float | None = None
    pr_auc: float | None = None
    brier: float | None = None


class EvaluationContext(BaseModel):
    model_version: str
    split: str
    threshold: float


class CalibrationBin(BaseModel):
    mean_predicted: float
    observed_rate: float
    n: int


class ModelMetricsResponse(BaseModel):
    models: list[ModelMetricRow] = Field(default_factory=list)
    comparison: list[Any] = Field(default_factory=list)
    evaluation_context: EvaluationContext | None = None
    confusion_matrix: list[list[int]] | None = None
    calibration: list[CalibrationBin] = Field(default_factory=list)
    dataset_notice: str


class ErrorResponse(BaseModel):
    detail: str
