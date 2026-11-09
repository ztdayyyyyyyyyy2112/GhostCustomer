import { AppHeader } from "@/components/AppHeader";
import { DataNotice } from "@/components/DataNotice";
import { Boxplots, Histogram } from "@/components/StatisticsCharts";
import { getStatistics } from "@/lib/api";

const number = (value: number | null) => value === null ? "—" : new Intl.NumberFormat("vi-VN", { maximumFractionDigits: 3 }).format(value);
const interval = (low: number | null, high: number | null) => low === null || high === null ? "—" : `[${number(low)}; ${number(high)}]`;
const pValue = (value: number | null) => value === null ? "—" : value < 0.001 ? "< 0,001" : number(value);

export default async function StatisticsPage() {
  const data = await getStatistics();
  const hasResults = data.groups.length > 0 || data.estimates.length > 0 || data.tests.length > 0;
  const boxplotSets = new Map<string, typeof data.groups>();
  for (const group of data.groups) {
    const key = JSON.stringify([group.metric, group.unit]);
    boxplotSets.set(key, [...(boxplotSets.get(key) ?? []), group]);
  }

  return <main className="dashboard-shell"><AppHeader current="statistics" /><div className="dashboard-content">
    <p className="eyebrow">PHÂN TÍCH / STATISTICS</p>
    <div className="title-row"><div><h1>Statistical Insights</h1><p className="subtitle">Phân phối, khoảng tin cậy và kiểm định được công bố cùng cỡ mẫu và giả định.</p></div></div>
    <DataNotice notice={data.dataset_notice} />
    {!hasResults ? <section className="empty-panel"><h2>Chưa có kết quả thống kê</h2><p>{data.dataset_notice}</p><p>Trang này sẽ nhận bảng và biểu đồ sau khi notebook phân tích chạy được trên dữ liệu đã chốt.</p></section> : <>
      {data.groups.length > 0 && <section className="analytics-section"><div className="section-heading"><div><p className="section-kicker">THỐNG KÊ MÔ TẢ</p><h2>Phân phối theo nhóm</h2></div></div><div className="chart-grid">{data.groups.map((group) => <Histogram key={`${group.name}-${group.metric}`} group={group} />)}{[...boxplotSets].map(([key, groups]) => <Boxplots key={key} groups={groups} />)}</div><div className="table-scroll"><table className="customer-table analytics-table"><thead><tr><th>Nhóm</th><th>Biến</th><th className="numeric">N</th><th className="numeric">Mean</th><th className="numeric">Median</th><th className="numeric">Q1–Q3</th></tr></thead><tbody>{data.groups.map((group) => <tr key={`${group.name}-${group.metric}`}><td>{group.name}</td><td>{group.metric} ({group.unit})</td><td className="numeric">{number(group.n)}</td><td className="numeric">{number(group.mean)}</td><td className="numeric">{number(group.median)}</td><td className="numeric">{interval(group.q1, group.q3)}</td></tr>)}</tbody></table></div></section>}
      {data.estimates.length > 0 && <section className="analytics-section"><p className="section-kicker">ƯỚC LƯỢNG</p><h2>Khoảng tin cậy</h2><div className="table-scroll"><table className="customer-table analytics-table"><thead><tr><th>Đại lượng</th><th className="numeric">N</th><th className="numeric">Ước lượng</th><th className="numeric">CI</th><th>Phương pháp</th></tr></thead><tbody>{data.estimates.map((item) => <tr key={item.name}><td>{item.name}</td><td className="numeric">{number(item.n)}</td><td className="numeric">{number(item.estimate)} {item.unit}</td><td className="numeric">{interval(item.ci_low, item.ci_high)}</td><td>{item.method}</td></tr>)}</tbody></table></div></section>}
      {data.tests.length > 0 && <section className="analytics-section"><p className="section-kicker">KIỂM ĐỊNH GIẢ THUYẾT</p><h2>Kết quả và giả định</h2><div className="table-scroll"><table className="customer-table analytics-table"><thead><tr><th>Kiểm định / giả thuyết</th><th className="numeric">N</th><th className="numeric">Statistic</th><th className="numeric">p-value</th><th className="numeric">Effect size</th><th className="numeric">CI</th><th>Giả định</th></tr></thead><tbody>{data.tests.map((test) => <tr key={`${test.name}-${test.hypothesis}`}><td><strong>{test.name}</strong><small className="table-subtext">{test.hypothesis} · {test.method}</small></td><td className="numeric">{number(test.n)}</td><td className="numeric">{number(test.statistic)}</td><td className="numeric">{pValue(test.p_value)}</td><td className="numeric">{number(test.effect_size)}</td><td className="numeric">{interval(test.ci_low, test.ci_high)}</td><td>{test.assumptions.length ? test.assumptions.join("; ") : "Chưa ghi"}</td></tr>)}</tbody></table></div></section>}
      {data.assumptions.length > 0 && <section className="analytics-section"><p className="section-kicker">LƯU Ý DIỄN GIẢI</p><ul className="assumption-list">{data.assumptions.map((item) => <li key={item}>{item}</li>)}</ul></section>}
    </>}
  </div></main>;
}
