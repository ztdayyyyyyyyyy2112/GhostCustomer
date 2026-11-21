import type { StatisticGroup } from "@/types/api";

const number = (value: number) => new Intl.NumberFormat("vi-VN", { maximumFractionDigits: 2 }).format(value);

export function Histogram({ group }: { group: StatisticGroup }) {
  const bins = group.histogram;
  if (bins.length === 0) return null;
  const highest = Math.max(1, ...bins.map((bin) => bin.count));

  return <figure className="chart-panel">
    <figcaption><strong>Phân phối {group.metric}</strong><span>{group.name} · n={number(group.n)} · {group.unit}</span></figcaption>
    <div className="histogram" role="img" aria-label={`Histogram ${group.metric} của ${group.name}`}>
      {bins.map((bin, index) => <div className="histogram-bin" key={`${bin.lower}-${bin.upper}-${index}`} title={`${number(bin.lower)}–${number(bin.upper)}: ${bin.count}`}>
        <span className="histogram-bar" style={{ height: `${bin.count / highest * 100}%` }} />
        <small>{number(bin.lower)}</small>
      </div>)}
    </div>
  </figure>;
}

export function Boxplots({ groups }: { groups: StatisticGroup[] }) {
  const completeGroups = groups.filter((group) => [group.min, group.q1, group.median, group.q3, group.max].every((value) => value !== null));
  const first = completeGroups[0];
  const complete = first ? completeGroups.filter((group) => group.metric === first.metric && group.unit === first.unit) : [];
  if (complete.length === 0) return null;
  const minimum = Math.min(...complete.map((group) => group.min as number));
  const maximum = Math.max(...complete.map((group) => group.max as number));
  const width = 590;
  const x = (value: number) => 10 + (value - minimum) / Math.max(maximum - minimum, 1) * width;

  return <figure className="chart-panel">
    <figcaption><strong>Boxplot {first.metric} theo nhóm</strong><span>Min · Q1 · Median · Q3 · Max</span></figcaption>
    <div className="boxplot-list">{complete.map((group) => <div className="boxplot-row" key={`${group.name}-${group.metric}`}>
      <span className="boxplot-label">{group.name} <small>n={number(group.n)}</small></span>
      <svg viewBox="0 0 610 44" role="img" aria-label={`Boxplot ${group.name}: min ${group.min}, Q1 ${group.q1}, median ${group.median}, Q3 ${group.q3}, max ${group.max}`}>
        <line x1={x(group.min!)} y1="22" x2={x(group.max!)} y2="22" stroke="#3f8990" strokeWidth="2" />
        <line x1={x(group.min!)} y1="13" x2={x(group.min!)} y2="31" stroke="#3f8990" strokeWidth="2" />
        <line x1={x(group.max!)} y1="13" x2={x(group.max!)} y2="31" stroke="#3f8990" strokeWidth="2" />
        <rect x={x(group.q1!)} y="11" width={Math.max(1, x(group.q3!) - x(group.q1!))} height="22" fill="#d9f2eb" stroke="#258d7c" />
        <line x1={x(group.median!)} y1="11" x2={x(group.median!)} y2="33" stroke="#124b52" strokeWidth="3" />
      </svg>
    </div>)}</div>
    <div className="boxplot-scale"><span>{number(minimum)}</span><span>{number(maximum)} {complete[0].unit}</span></div>
  </figure>;
}
