import Link from "next/link";
import { isMockMode } from "@/lib/api";

export function AppHeader({ current }: { current: "dashboard" | "customers" }) {
  return (
    <header className="dashboard-header">
      <Link href="/dashboard" className="brand" aria-label="Ghost Customer, về trang tổng quan">
        <span className="brand-mark">G</span>
        <span>GHOST CUSTOMER <small>STAT3013</small></span>
      </Link>
      <nav className="main-nav" aria-label="Điều hướng chính">
        <Link href="/dashboard" aria-current={current === "dashboard" ? "page" : undefined}>Tổng quan</Link>
        <Link href="/customers" aria-current={current === "customers" ? "page" : undefined}>Khách hàng</Link>
      </nav>
      <span className="mode-badge">{isMockMode() ? "CHẾ ĐỘ MOCK" : "DỮ LIỆU API"}</span>
    </header>
  );
}
