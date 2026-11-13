import type { ForecastResponse, SeriesPoint } from "@/types/api";

export function ForecastChart({ forecast }: { forecast: ForecastResponse }) {
  const fitted = forecast.fitted ?? [];
  const dates = [...new Set([...forecast.history, ...fitted, ...forecast.predictions, ...forecast.lower_ci, ...forecast.upper_ci].map((point) => point.date))].sort();
  if (dates.length === 0) return null;

  const values = [...forecast.history, ...fitted, ...forecast.predictions, ...forecast.lower_ci, ...forecast.upper_ci].map((point) => point.value);
  const minimum = Math.min(0, ...values);
  const maximum = Math.max(1, ...values);
  const left = 55, right = 775, top = 22, bottom = 270;
  const firstTime = Date.parse(`${dates[0]}T00:00:00Z`);
  const lastTime = Date.parse(`${dates[dates.length - 1]}T00:00:00Z`);
  const useDateScale = dates.every((date) => Number.isFinite(Date.parse(`${date}T00:00:00Z`))) && lastTime > firstTime;
  const x = (date: string) => left + (useDateScale
    ? (Date.parse(`${date}T00:00:00Z`) - firstTime) / (lastTime - firstTime)
    : dates.indexOf(date) / Math.max(dates.length - 1, 1)) * (right - left);
  const y = (value: number) => bottom - (value - minimum) / Math.max(maximum - minimum, 0.001) * (bottom - top);
  const points = (series: SeriesPoint[]) => [...series].sort((a, b) => a.date.localeCompare(b.date)).map((point) => `${x(point.date)},${y(point.value)}`).join(" ");
  const lower = new Map(forecast.lower_ci.map((point) => [point.date, point.value]));
  const upper = new Map(forecast.upper_ci.map((point) => [point.date, point.value]));
  const ciDates = dates.filter((date) => lower.has(date) && upper.has(date));
  const ciPoints = [...ciDates.map((date) => `${x(date)},${y(upper.get(date)!)}`), ...[...ciDates].reverse().map((date) => `${x(date)},${y(lower.get(date)!)}`)].join(" ");
  const split = forecast.train_end && dates.includes(forecast.train_end) ? x(forecast.train_end) : null;

  return <figure className="forecast-figure">
    <svg viewBox="0 0 800 320" role="img" aria-label="Biểu đồ tỷ lệ Ghost quan sát, giá trị fitted và dự báo theo thời gian">
      <line x1={left} y1={bottom} x2={right} y2={bottom} stroke="#a5b8bf" />
      {[0, 0.25, 0.5, 0.75, 1].map((tick) => <g key={tick}><line x1={left} y1={y(tick)} x2={right} y2={y(tick)} stroke="#e5edef" /><text x="45" y={y(tick) + 4} textAnchor="end" fill="#69808b" fontSize="11">{Math.round(tick * 100)}%</text></g>)}
      {ciDates.length > 1 && <polygon points={ciPoints} fill="#d6f1e8" opacity="0.8" />}
      {split !== null && <g><line x1={split} y1={top} x2={split} y2={bottom} stroke="#8b9ca3" strokeDasharray="5 5" /><text x={split + 5} y="36" fill="#657985" fontSize="10">Train end</text></g>}
      {forecast.history.length > 1 && <polyline points={points(forecast.history)} fill="none" stroke="#1f7890" strokeWidth="3" strokeLinejoin="round" />}
      {fitted.length > 1 && <polyline points={points(fitted)} fill="none" stroke="#e3a442" strokeWidth="2" strokeDasharray="6 4" />}
      {forecast.predictions.length > 1 && <polyline points={points(forecast.predictions)} fill="none" stroke="#208b70" strokeWidth="3" strokeLinejoin="round" />}
      {forecast.history.map((point) => <circle key={`h-${point.date}`} cx={x(point.date)} cy={y(point.value)} r="3" fill="#1f7890" />)}
      {forecast.predictions.map((point) => <circle key={`p-${point.date}`} cx={x(point.date)} cy={y(point.value)} r="3" fill="#208b70" />)}
      <text x={left} y="300" fill="#69808b" fontSize="11">{dates[0]}</text>
      <text x={right} y="300" fill="#69808b" textAnchor="end" fontSize="11">{dates[dates.length - 1]}</text>
    </svg>
    <figcaption className="chart-legend"><span><i className="legend-actual" />Quan sát</span><span><i className="legend-fitted" />Fitted</span><span><i className="legend-forecast" />Dự báo</span><span><i className="legend-ci" />Khoảng tin cậy</span></figcaption>
  </figure>;
}
