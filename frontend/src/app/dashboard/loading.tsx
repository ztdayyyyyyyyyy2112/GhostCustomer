export default function Loading() {
  return <main className="dashboard-shell"><div className="dashboard-content"><p className="eyebrow">TỔNG QUAN / OVERVIEW</p><div className="loading-bar" /><div className="loading-grid">{Array.from({ length: 5 }, (_, i) => <div className="loading-card" key={i} />)}</div></div></main>;
}
