import { KpiCard } from "@/components/KpiCard";
import { getOverview, isMockMode } from "@/lib/api";

const percent = (value: number | null) => value === null ? "Chưa đủ dữ liệu" : `${(value * 100).toFixed(1)}%`;

export default async function DashboardPage() {
  const overview = await getOverview();
  return <main className="dashboard-shell">
    <header className="dashboard-header"><div className="brand"><span className="brand-mark">G</span><span>GHOST CUSTOMER <small>STAT3013</small></span></div><span className="mode-badge">{isMockMode() ? "CHẾ ĐỘ MOCK" : "DỮ LIỆU API"}</span></header>
    <div className="dashboard-content">
      <p className="eyebrow">TỔNG QUAN / OVERVIEW</p>
      <div className="title-row"><div><h1>Hành vi khách hàng</h1><p className="subtitle">Quan sát mức độ tương tác và trạng thái vận hành theo từng mốc dữ liệu.</p></div><div className="date-chip">{overview.date_range ? `${overview.date_range.start} → ${overview.date_range.end}` : "Chưa có khoảng thời gian"}</div></div>
      <div className="notice" role="status"><strong>{overview.dataset_notice}</strong><span>“Ghost” là nhãn vận hành do nhóm định nghĩa; chưa phải bằng chứng khách hàng đã rời bỏ.</span></div>
      {overview.total_customers === 0 ? <section className="empty-panel"><h2>Chưa có khách hàng</h2><p>Dashboard sẽ hiển thị khi nguồn dữ liệu có bản ghi hợp lệ.</p></section> : <>
        <section aria-label="Chỉ số tổng quan" className="kpi-grid">
          <KpiCard label="Tổng khách hàng" value={overview.total_customers.toLocaleString("vi-VN")} note="Trong tập đang hiển thị" />
          <KpiCard label="Đang hoạt động" value={overview.active_count.toLocaleString("vi-VN")} note={`Tỷ lệ ${percent(overview.active_rate)}`} />
          <KpiCard label="Ghost" value={overview.ghost_count.toLocaleString("vi-VN")} note="Theo nhãn vận hành" accent />
          <KpiCard label="Cần theo dõi" value={overview.candidate_count.toLocaleString("vi-VN")} note="Candidate" />
          <KpiCard label="Chưa xác định" value={overview.unknown_count.toLocaleString("vi-VN")} note="Thiếu thông tin/horizon" />
        </section>
        <section className="summary-grid"><article className="summary-panel"><p className="section-kicker">TỶ LỆ GHOST</p><h2>{percent(overview.ghost_rate)}</h2><div className="rate-track"><span style={{ width: `${Math.max(0, Math.min(100, (overview.ghost_rate ?? 0) * 100))}%` }} /></div><p>Mẫu số tạm thời là tổng khách hàng trong response. Quy tắc cohort cuối cùng cần được chốt sau data audit.</p></article><article className="summary-panel"><p className="section-kicker">TRẠNG THÁI NGHIÊN CỨU</p><h2>Đang chuẩn bị dữ liệu</h2><p>Chưa công bố kiểm định, khoảng tin cậy, chất lượng mô hình hay dự báo. Những kết quả đó sẽ được nối vào dashboard sau khi pipeline chạy lại được.</p></article></section>
      </>}
    </div>
  </main>;
}
