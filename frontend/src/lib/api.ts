import mock from "@/mocks/data.json";
import type { Customer, CustomerDetailResponse, CustomersResponse, CustomerStatus, ForecastResponse, ModelMetricsResponse, OverviewResponse, PredictRequest, PredictResponse, StatisticsResponse } from "@/types/api";

const mode = process.env.NEXT_PUBLIC_API_MODE ?? "mock";
const baseUrl = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").replace(/\/$/, "");
export const isMockMode = () => mode !== "real";

export class ApiError extends Error {
  constructor(message: string, public readonly status: number) {
    super(message);
    this.name = "ApiError";
  }
}

async function mockDelay() {
  await new Promise((resolve) => setTimeout(resolve, 250));
  if (process.env.NEXT_PUBLIC_MOCK_ERROR === "1") throw new Error("Lỗi mô phỏng để kiểm tra giao diện.");
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${baseUrl}/api${path}`, { cache: "no-store", ...init });
  if (!response.ok) {
    const body: unknown = await response.json().catch(() => null);
    const detail = typeof body === "object" && body !== null && "detail" in body && typeof body.detail === "string" ? body.detail : `API trả về HTTP ${response.status}`;
    throw new ApiError(detail, response.status);
  }
  return (await response.json()) as T;
}

export async function getOverview(): Promise<OverviewResponse> {
  if (!isMockMode()) return request("/overview");
  await mockDelay(); return mock.overview;
}

export interface CustomerQuery {
  page?: number; page_size?: number; status?: CustomerStatus; search?: string;
  sort?: "snapshot_date" | "sessions" | "views" | "decay" | "risk_score"; order?: "asc" | "desc";
}

export async function getCustomers(query: CustomerQuery = {}): Promise<CustomersResponse> {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(query)) if (value !== undefined && value !== "") params.set(key, String(value));
  if (!isMockMode()) return request(`/customers?${params}`);
  await mockDelay();
  const page = Math.max(1, query.page ?? 1), size = Math.min(100, Math.max(1, query.page_size ?? 20));
  let items = mock.customers as Customer[];
  if (query.status) items = items.filter((item) => item.status === query.status);
  if (query.search) items = items.filter((item) => item.customer_id.toLowerCase().includes(query.search!.toLowerCase()));
  if (query.sort) {
    const key = query.sort, direction = query.order === "asc" ? 1 : -1;
    items = [...items].sort((a, b) => {
      const left = a[key], right = b[key];
      if (left === null && right === null) return 0;
      if (left === null) return 1;
      if (right === null) return -1;
      return left < right ? -direction : left > right ? direction : 0;
    });
  }
  return { items: items.slice((page - 1) * size, page * size), page, page_size: size, total: items.length };
}

export async function getCustomer(id: string): Promise<CustomerDetailResponse> {
  if (!isMockMode()) return request(`/customers/${encodeURIComponent(id)}`);
  await mockDelay();
  const customer = (mock.customers as Customer[]).find((item) => item.customer_id === id);
  if (!customer) throw new ApiError(`Không tìm thấy khách hàng ${id}`, 404);
  return { customer, current_features: { sessions_4w: customer.sessions, views_4w: customer.views }, weekly_timeline: customer.customer_id === "C001" ? mock.weekly_timeline as CustomerDetailResponse["weekly_timeline"] : [], status: customer.status };
}

export async function getStatistics(): Promise<StatisticsResponse> {
  if (!isMockMode()) return request("/statistics");
  await mockDelay(); return mock.statistics;
}
export async function getForecast(): Promise<ForecastResponse> {
  if (!isMockMode()) return request("/forecast");
  await mockDelay(); return mock.forecast;
}
export async function predict(input: PredictRequest): Promise<PredictResponse> {
  if (!isMockMode()) return request("/predict", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(input) });
  await mockDelay(); return mock.prediction;
}
export async function getModelMetrics(): Promise<ModelMetricsResponse> {
  if (!isMockMode()) return request("/model/metrics");
  await mockDelay(); return mock.metrics;
}
