import Link from "next/link";

export default function NotFound() {
  return <section className="empty-panel"><h1>Không tìm thấy khách hàng</h1><p>Kiểm tra lại mã khách hàng hoặc chọn từ danh sách.</p><Link className="text-link" href="/customers">Về danh sách khách hàng</Link></section>;
}
