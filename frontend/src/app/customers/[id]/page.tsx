import Link from "next/link";
import { notFound } from "next/navigation";
import { Suspense } from "react";
import { AppHeader } from "@/components/AppHeader";
import { CustomerStatusBadge } from "@/components/CustomerStatusBadge";
import { DataNotice } from "@/components/DataNotice";
import { ApiError, getCustomer } from "@/lib/api";
import type { CustomerWeekly } from "@/types/api";

const featureLabels: Record<string, string> = {
  sessions_4w: "Số phiên 4 tuần trước T",
  views_4w: "Lượt xem 4 tuần trước T",
  days_since_last_view: "Số ngày từ lượt xem gần nhất",
};

const phaseLabels: Record<CustomerWeekly["phase"], string> = {
  baseline: "Baseline",
  observation: "Observation",
  confirmation: "Confirmation",
};

function metric(value: number | null) {
  return value === null ? "Chưa có dữ liệu" : value.toLocaleString("vi-VN");
}

function rate(value: number | null) {
  return value === null ? "Chưa có dữ liệu" : `${(value * 100).toFixed(1)}%`;
}

function Timeline({ rows, emptyText, maxViews }: { rows: CustomerWeekly[]; emptyText: string; maxViews: number }) {
  if (rows.length === 0) return <p className="muted-text">{emptyText}</p>;
  return <div className="timeline-list">{rows.map((row) => <div className="timeline-row" key={`${row.week_start}-${row.phase}`}>
    <div className="timeline-meta"><time dateTime={row.week_start}>{row.week_start}</time><span className={`phase-tag phase-${row.phase}`}>{phaseLabels[row.phase]}</span></div>
    <div className="timeline-data"><div className="timeline-track" role="img" aria-label={`${row.views} lượt xem trong tuần ${row.week_start}`}><span style={{ width: `${row.views / maxViews * 100}%` }} /></div><strong>{row.views} lượt xem</strong><small>{row.sessions} phiên · {row.carts} giỏ hàng · {row.purchases} giao dịch</small></div>
  </div>)}</div>;
}

async function CustomerContent({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  let detail;
  try {
    detail = await getCustomer(id);
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) notFound();
    throw error;
  }

  const { customer, current_features, weekly_timeline } = detail;
  const beforeT = weekly_timeline.filter((row) => row.phase !== "confirmation");
  const afterT = weekly_timeline.filter((row) => row.phase === "confirmation");
  const maxViews = Math.max(1, ...weekly_timeline.map((row) => row.views));

  return <>
    <Link href="/customers" className="back-link">← Trở lại danh sách</Link>
    <div className="title-row detail-title"><div><p className="eyebrow">HỒ SƠ KHÁCH HÀNG</p><h1>{customer.customer_id}</h1><p className="subtitle">Snapshot tại mốc T: <time dateTime={customer.snapshot_date}>{customer.snapshot_date}</time>. Các đặc trưng dự đoán chỉ lấy từ sự kiện đến mốc này.</p></div><CustomerStatusBadge status={detail.status} /></div>
    <DataNotice />

    <section className="detail-summary" aria-label="Thông tin tại mốc T">
      <div><span>Trạng thái</span><strong><CustomerStatusBadge status={detail.status} /></strong></div>
      <div><span>Số phiên</span><strong>{metric(customer.sessions)}</strong></div>
      <div><span>Lượt xem</span><strong>{metric(customer.views)}</strong></div>
      <div><span>Mức suy giảm</span><strong>{rate(customer.decay)}</strong></div>
      <div><span>Risk score</span><strong>{rate(customer.risk_score)}</strong></div>
    </section>

    <div className="detail-grid">
      <section className="summary-panel"><p className="section-kicker">CHỈ SỐ TRƯỚC MỐC T</p><h2>Đặc trưng dự đoán</h2><p>Chỉ các sự kiện đến ngày snapshot mới được phép xuất hiện ở đây.</p>{Object.entries(current_features).length === 0 ? <p className="muted-text">Chưa có đặc trưng khả dụng.</p> : <dl className="feature-list">{Object.entries(current_features).map(([key, value]) => <div key={key}><dt>{featureLabels[key] ?? key}</dt><dd>{metric(value)}</dd></div>)}</dl>}</section>
      <section className="summary-panel"><p className="section-kicker">CÁCH ĐỌC KẾT QUẢ</p><h2>Trạng thái vận hành</h2><p>Nhãn Ghost được xác định theo quy tắc tương lai của nhóm và còn chờ quyết định sau data audit. Risk score, nếu có, là ước lượng xác suất, không phải khẳng định chắc chắn.</p>{detail.status === "unknown" && <p className="muted-text">Khách hàng này chưa đủ thông tin để xác định nhãn.</p>}</section>
    </div>

    <section className="timeline-panel"><div className="section-heading"><div><p className="section-kicker">LỊCH SỬ THEO TUẦN</p><h2>Baseline và observation</h2></div><span>Chỉ dữ liệu trước hoặc tại T</span></div><Timeline rows={beforeT} maxViews={maxViews} emptyText="Chưa có lịch sử tuần trước T cho khách hàng này." /></section>
    <section className="timeline-panel future-panel"><div className="section-heading"><div><p className="section-kicker">CỬA SỔ XÁC NHẬN</p><h2>Confirmation sau T</h2></div><span>Không đưa vào đặc trưng dự đoán</span></div><Timeline rows={afterT} maxViews={maxViews} emptyText="Chưa có dữ liệu xác nhận tương lai; không suy diễn khách hàng đã churn." /></section>
  </>;
}

export default function CustomerDetailPage({ params }: { params: Promise<{ id: string }> }) {
  return <main className="dashboard-shell"><AppHeader current="customers" /><div className="dashboard-content"><Suspense fallback={<div className="loading-bar" aria-label="Đang tải hồ sơ" />}><CustomerContent params={params} /></Suspense></div></main>;
}
