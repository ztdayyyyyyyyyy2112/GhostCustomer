export function KpiCard({ label, value, note, accent = false }: { label: string; value: string; note?: string; accent?: boolean }) {
  return <article className={`kpi-card${accent ? " kpi-card-accent" : ""}`}><p className="kpi-label">{label}</p><p className="kpi-value">{value}</p>{note && <p className="kpi-note">{note}</p>}</article>;
}
