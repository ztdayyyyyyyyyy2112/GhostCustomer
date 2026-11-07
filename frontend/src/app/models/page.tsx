import { AppHeader } from "@/components/AppHeader";
import { DataNotice } from "@/components/DataNotice";
import { getModelMetrics } from "@/lib/api";

const percentage = (value: number | null) => value === null ? "—" : `${(value * 100).toFixed(1)}%`;
const number = (value: number) => new Intl.NumberFormat("vi-VN").format(value);

export default async function ModelsPage() {
  const metrics = await getModelMetrics();
  const matrix = metrics.confusion_matrix;
  const hasMatrix = matrix?.length === 2 && matrix.every((row) => row.length === 2);
  const context = metrics.evaluation_context;

  return <main className="dashboard-shell"><AppHeader current="models" /><div className="dashboard-content">
    <p className="eyebrow">ĐÁNH GIÁ / MODEL METRICS</p>
    <div className="title-row"><div><h1>Chất lượng mô hình</h1><p className="subtitle">So sánh trên tập kiểm thử giữ nguyên, kèm cỡ mẫu, tỷ lệ lớp và ngưỡng phân loại.</p></div></div>
    <DataNotice />
    {metrics.models.length === 0 ? <section className="empty-panel"><h2>Chưa có đánh giá mô hình</h2><p>{metrics.dataset_notice}</p><p>Trang này không dùng accuracy hoặc số liệu mock làm bằng chứng hiệu quả.</p></section> : <>
      <section className="analytics-section"><p className="section-kicker">SO SÁNH MÔ HÌNH</p><h2>Kết quả theo split</h2><div className="table-scroll"><table className="customer-table analytics-table"><thead><tr><th>Mô hình</th><th>Split</th><th className="numeric">N</th><th className="numeric">Prevalence</th><th className="numeric">Threshold</th><th className="numeric">Precision</th><th className="numeric">Recall</th><th className="numeric">F1</th><th className="numeric">ROC-AUC</th><th className="numeric">PR-AUC</th><th className="numeric">Brier</th></tr></thead><tbody>{metrics.models.map((model) => <tr key={`${model.name}-${model.model_version}-${model.split}`}><td><strong>{model.name}</strong><small className="table-subtext">{model.model_version}</small></td><td>{model.split}</td><td className="numeric">{number(model.support)}</td><td className="numeric">{percentage(model.prevalence)}</td><td className="numeric">{percentage(model.threshold)}</td><td className="numeric">{percentage(model.precision)}</td><td className="numeric">{percentage(model.recall)}</td><td className="numeric">{percentage(model.f1)}</td><td className="numeric">{percentage(model.roc_auc)}</td><td className="numeric">{percentage(model.pr_auc)}</td><td className="numeric">{model.brier?.toFixed(3) ?? "—"}</td></tr>)}</tbody></table></div><p className="source-note">{metrics.dataset_notice}</p></section>
      {hasMatrix && context && <section className="analytics-section"><p className="section-kicker">MA TRẬN NHẦM LẪN</p><h2>Nhìn theo nhãn thực tế</h2><p className="source-note">{context.model_version} · {context.split} · ngưỡng {percentage(context.threshold)}</p><div className="table-scroll"><table className="customer-table analytics-table matrix-table"><thead><tr><th></th><th>Dự đoán non-ghost</th><th>Dự đoán ghost</th></tr></thead><tbody><tr><th>Thực tế non-ghost</th><td>{number(matrix[0][0])} TN</td><td>{number(matrix[0][1])} FP</td></tr><tr><th>Thực tế ghost</th><td>{number(matrix[1][0])} FN</td><td>{number(matrix[1][1])} TP</td></tr></tbody></table></div></section>}
      {metrics.calibration.length > 0 && context && <section className="analytics-section"><p className="section-kicker">HIỆU CHUẨN XÁC SUẤT</p><h2>Calibration bins</h2><p className="source-note">{context.model_version} · {context.split}</p><div className="table-scroll"><table className="customer-table analytics-table"><thead><tr><th>Mean predicted</th><th>Observed rate</th><th className="numeric">N</th></tr></thead><tbody>{metrics.calibration.map((bin, index) => <tr key={index}><td>{percentage(bin.mean_predicted)}</td><td>{percentage(bin.observed_rate)}</td><td className="numeric">{number(bin.n)}</td></tr>)}</tbody></table></div></section>}
    </>}
  </div></main>;
}
