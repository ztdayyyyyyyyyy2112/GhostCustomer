import Link from "next/link";
import { isMockMode } from "@/lib/api";

type Section = "dashboard" | "customers" | "statistics" | "forecast" | "predict" | "models";

export function AppHeader({ current }: { current: Section }) {
  return (
    <header className="dashboard-header">
      <Link href="/dashboard" className="brand" aria-label="Ghost Customer, về trang tổng quan">
        <span className="brand-mark">G</span>
        <span>GHOST CUSTOMER <small>STAT3013</small></span>
      </Link>
      <nav className="main-nav" aria-label="Điều hướng chính">
        <Link href="/dashboard" aria-current={current === "dashboard" ? "page" : undefined}>Tổng quan</Link>
        <Link href="/customers" aria-current={current === "customers" ? "page" : undefined}>Khách hàng</Link>
        <Link href="/statistics" aria-current={current === "statistics" ? "page" : undefined}>Thống kê</Link>
        <Link href="/forecast" aria-current={current === "forecast" ? "page" : undefined}>Dự báo</Link>
        <Link href="/predict" aria-current={current === "predict" ? "page" : undefined}>Dự đoán</Link>
        <Link href="/models" aria-current={current === "models" ? "page" : undefined}>Mô hình</Link>
      </nav>
      <span className="mode-badge">{isMockMode() ? "CHẾ ĐỘ MOCK" : "DỮ LIỆU API"}</span>
    </header>
  );
}
