"use client";

export default function Error({ error, reset }: { error: Error; reset: () => void }) {
  return <main className="dashboard-shell"><div className="dashboard-content"><section className="empty-panel"><h1>Không tải được danh sách khách hàng</h1><p>{error.message}</p><button className="retry-button" onClick={reset}>Thử lại</button></section></div></main>;
}
