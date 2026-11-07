import Link from "next/link";
import { Suspense } from "react";
import { AppHeader } from "@/components/AppHeader";
import { CustomerStatusBadge, statusLabels } from "@/components/CustomerStatusBadge";
import { DataNotice } from "@/components/DataNotice";
import { getCustomers, type CustomerQuery } from "@/lib/api";
import type { CustomerStatus } from "@/types/api";

type RawParams = Record<string, string | string[] | undefined>;
type SortKey = NonNullable<CustomerQuery["sort"]>;

const statuses = Object.keys(statusLabels) as CustomerStatus[];
const sortOptions: { value: SortKey; label: string }[] = [
  { value: "snapshot_date", label: "Ngày snapshot" },
  { value: "sessions", label: "Số phiên" },
  { value: "views", label: "Lượt xem" },
  { value: "decay", label: "Mức suy giảm" },
  { value: "risk_score", label: "Điểm rủi ro" },
];

function first(value: string | string[] | undefined) {
  return Array.isArray(value) ? value[0] : value;
}

function positiveInt(value: string | undefined, fallback: number, maximum: number) {
  const parsed = Number(value);
  return Number.isSafeInteger(parsed) && parsed >= 1 && parsed <= maximum ? parsed : fallback;
}

function parseQuery(raw: RawParams): Required<Pick<CustomerQuery, "page" | "page_size" | "sort" | "order">> & Pick<CustomerQuery, "status" | "search"> {
  const status = first(raw.status);
  const sort = first(raw.sort);
  return {
    page: positiveInt(first(raw.page), 1, 100_000),
    page_size: positiveInt(first(raw.page_size), 10, 100),
    status: statuses.includes(status as CustomerStatus) ? status as CustomerStatus : undefined,
    search: first(raw.search)?.trim().slice(0, 80) || undefined,
    sort: sortOptions.some((option) => option.value === sort) ? sort as SortKey : "snapshot_date",
    order: first(raw.order) === "asc" ? "asc" : "desc",
  };
}

function pageHref(query: CustomerQuery, page: number) {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries({ ...query, page })) {
    if (value !== undefined && value !== "") params.set(key, String(value));
  }
  return `/customers?${params}`;
}

function count(value: number | null) {
  return value === null ? "—" : value.toLocaleString("vi-VN");
}

function percentage(value: number | null) {
  return value === null ? "—" : `${(value * 100).toFixed(1)}%`;
}

async function CustomersContent({ searchParams }: { searchParams: Promise<RawParams> }) {
  const query = parseQuery(await searchParams);
  const result = await getCustomers(query);
  const totalPages = Math.max(1, Math.ceil(result.total / result.page_size));
  const firstItem = result.total === 0 ? 0 : (result.page - 1) * result.page_size + 1;
  const lastItem = Math.min(result.page * result.page_size, result.total);

  return (
    <>
      <div className="title-row">
        <div>
          <h1>Danh sách khách hàng</h1>
          <p className="subtitle">
            Tìm và xem từng snapshot. Điểm rủi ro chỉ là xác suất ước lượng của mô hình khi đã có model hợp lệ.
          </p>
        </div>
        <span className="date-chip">{result.total.toLocaleString("vi-VN")} kết quả</span>
      </div>
      <DataNotice />
      <form className="filter-panel" action="/customers" method="get" aria-label="Tìm kiếm và lọc khách hàng">
        <label className="filter-field filter-search">
          Mã khách hàng
          <input
            name="search"
            type="search"
            defaultValue={query.search ?? ""}
            placeholder="Ví dụ: C001"
            aria-label="Tìm kiếm theo mã khách hàng"
          />
        </label>
        <label className="filter-field">
          Trạng thái
          <select name="status" defaultValue={query.status ?? ""} aria-label="Lọc theo trạng thái">
            <option value="">Tất cả</option>
            {statuses.map((status) => (
              <option value={status} key={status}>
                {statusLabels[status]}
              </option>
            ))}
          </select>
        </label>
        <label className="filter-field">
          Sắp xếp theo
          <select name="sort" defaultValue={query.sort} aria-label="Chọn trường sắp xếp">
            {sortOptions.map((option) => (
              <option value={option.value} key={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>
        <label className="filter-field">
          Thứ tự
          <select name="order" defaultValue={query.order} aria-label="Thứ tự hiển thị">
            <option value="desc">Giảm dần</option>
            <option value="asc">Tăng dần</option>
          </select>
        </label>
        <label className="filter-field filter-size">
          Mỗi trang
          <select name="page_size" defaultValue={query.page_size} aria-label="Số dòng mỗi trang">
            <option value="2">2</option>
            <option value="10">10</option>
            <option value="20">20</option>
            <option value="50">50</option>
          </select>
        </label>
        <button type="submit" className="primary-button" aria-label="Áp dụng bộ lọc">
          Áp dụng
        </button>
      </form>

      {result.items.length === 0 ? (
        <section className="empty-panel" aria-live="polite">
          <h2>Không có khách hàng phù hợp</h2>
          <p>Thử tìm mã khác hoặc bỏ bộ lọc hiện tại.</p>
          <Link className="text-link" href="/customers">
            Xóa bộ lọc
          </Link>
        </section>
      ) : (
        <section className="table-panel" aria-label="Bảng khách hàng">
          <div className="table-scroll">
            <table className="customer-table">
              <thead>
                <tr>
                  <th scope="col">Khách hàng</th>
                  <th scope="col">Snapshot</th>
                  <th scope="col">Trạng thái</th>
                  <th scope="col" className="numeric">Phiên</th>
                  <th scope="col" className="numeric">Lượt xem</th>
                  <th scope="col" className="numeric">Suy giảm</th>
                  <th scope="col" className="numeric">Risk score</th>
                  <th scope="col"><span className="sr-only">Chi tiết</span></th>
                </tr>
              </thead>
              <tbody>
                {result.items.map((customer) => (
                  <tr key={`${customer.customer_id}-${customer.snapshot_date}`}>
                    <td className="customer-id">{customer.customer_id}</td>
                    <td>{customer.snapshot_date}</td>
                    <td><CustomerStatusBadge status={customer.status} /></td>
                    <td className="numeric">{count(customer.sessions)}</td>
                    <td className="numeric">{count(customer.views)}</td>
                    <td className="numeric">{percentage(customer.decay)}</td>
                    <td className="numeric">{percentage(customer.risk_score)}</td>
                    <td>
                      <Link
                        className="row-link"
                        href={`/customers/${encodeURIComponent(customer.customer_id)}`}
                        aria-label={`Xem chi tiết khách hàng ${customer.customer_id}`}
                      >
                        Xem chi tiết<span aria-hidden="true"> →</span>
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <footer className="table-footer">
            <p>
              Hiển thị {firstItem}–{lastItem} / {result.total} khách hàng
            </p>
            <nav className="pagination" aria-label="Phân trang">
              {query.page > 1 && (
                <Link href={pageHref(query, query.page - 1)} aria-label="Trang trước">
                  ← Trước
                </Link>
              )}
              <span>
                Trang {query.page} / {totalPages}
              </span>
              {query.page < totalPages && (
                <Link href={pageHref(query, query.page + 1)} aria-label="Trang kế tiếp">
                  Sau →
                </Link>
              )}
            </nav>
          </footer>
        </section>
      )}
    </>
  );
}

export default function CustomersPage({ searchParams }: { searchParams: Promise<RawParams> }) {
  return (
    <main className="dashboard-shell">
      <AppHeader current="customers" />
      <div className="dashboard-content">
        <p className="eyebrow">KHÁCH HÀNG / CUSTOMERS</p>
        <Suspense fallback={<div className="loading-bar" aria-label="Đang tải danh sách" />}>
          <CustomersContent searchParams={searchParams} />
        </Suspense>
      </div>
    </main>
  );
}
