export type CustomerStatus =
  | "active"
  | "ghost"
  | "candidate"
  | "recovered"
  | "inactive"
  | "unknown";

export interface Customer {
  customer_id: string;
  snapshot_date: string;
  status: CustomerStatus;
  sessions: number | null;
  views: number | null;
  decay: number | null;
  risk_score: number | null;
}

export interface CustomerWeekly {
  week_start: string;
  views: number;
  carts: number;
  purchases: number;
  sessions: number;
  active_days: number;
  phase: "baseline" | "observation" | "confirmation";
}

export interface OverviewResponse {
  total_customers: number;
  active_count: number;
  ghost_count: number;
  candidate_count: number;
  unknown_count: number;
  inactive_count: number;
  recovered_count: number;
  active_rate: number | null;
  ghost_rate: number | null;
  date_range: { start: string; end: string } | null;
  dataset_notice: string;
}

export interface CustomersResponse {
  items: Customer[];
  page: number;
  page_size: number;
  total: number;
}

export interface CustomerDetailResponse {
  customer: Customer;
  current_features: Record<string, number | null>;
  weekly_timeline: CustomerWeekly[];
  status: CustomerStatus;
}

export interface StatsResult {
  name: string;
  hypothesis: string;
  n: number;
  statistic: number | null;
  p_value: number | null;
  effect_size: number | null;
  ci_low: number | null;
  ci_high: number | null;
  method: string;
  assumptions: string[];
}

export interface StatisticGroup {
  name: string;
  metric: string;
  unit: string;
  n: number;
  mean: number | null;
  median: number | null;
  q1: number | null;
  q3: number | null;
  min: number | null;
  max: number | null;
  histogram: { lower: number; upper: number; count: number }[];
}

export interface StatisticEstimate {
  name: string;
  n: number;
  estimate: number;
  ci_low: number | null;
  ci_high: number | null;
  method: string;
  unit: string;
}

export interface StatisticsResponse {
  groups: StatisticGroup[];
  estimates: StatisticEstimate[];
  tests: StatsResult[];
  p_values: number[];
  cis: unknown[];
  assumptions: string[];
  dataset_notice: string;
}

export interface SeriesPoint { date: string; value: number }

export interface ForecastResponse {
  history: SeriesPoint[];
  fitted?: SeriesPoint[];
  predictions: SeriesPoint[];
  lower_ci: SeriesPoint[];
  upper_ci: SeriesPoint[];
  method: string | null;
  mae: number | null;
  rmse: number | null;
  smape: number | null;
  train_end?: string | null;
  unit?: "day" | "week" | null;
  series_length?: number | null;
  dataset_notice: string;
}

export type PredictRequest =
  | { customer_id: string; snapshot_date: string }
  | { features: Record<string, number | null> };

export interface PredictResponse {
  score: number;
  risk_label: string;
  top_factors: { feature: string; contribution: number }[];
  model_version: string;
  dataset_notice: string;
}

export interface ModelMetricsResponse {
  models: {
    name: string;
    model_version: string;
    split: string;
    support: number;
    prevalence: number;
    threshold: number | null;
    precision: number | null;
    recall: number | null;
    f1: number | null;
    roc_auc: number | null;
    pr_auc: number | null;
    brier: number | null;
  }[];
  comparison: unknown[];
  evaluation_context: { model_version: string; split: string; threshold: number } | null;
  confusion_matrix: number[][] | null;
  calibration: { mean_predicted: number; observed_rate: number; n: number }[];
  dataset_notice: string;
}
