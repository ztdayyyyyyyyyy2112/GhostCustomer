import { AppHeader } from "@/components/AppHeader";
import { DataNotice } from "@/components/DataNotice";
import { ForecastChart } from "@/components/ForecastChart";
import { getForecast } from "@/lib/api";

const metric = (value: number | null) => value === null ? "Chưa có" : new Intl.NumberFormat("vi-VN", { maximumFractionDigits: 3 }).format(value);
const percentagePoints = (value: number | null) => value === null ? "Chưa có" : `${metric(value * 100)} điểm %`;

export default async function ForecastPage() {
  const forecast = await getForecast();
  const hasSeries = forecast.history.length > 0 || forecast.predictions.length > 0;

  return <main className="dashboard-shell"><AppHeader current="forecast" /><div className="dashboard-content">
    <p className="eyebrow">DỰ BÁO / FORECASTING</p>
    <div className="title-row"><div><h1>Dự báo tỷ lệ Ghost</h1><p className="subtitle">Phân biệt tỷ lệ quan sát, giá trị fitted và dự báo tương lai theo thời gian.</p></div></div>
    <DataNotice notice={forecast.dataset_notice} />
    {!hasSeries ? <section className="empty-panel"><h2>Chưa có chuỗi dự báo</h2><p>{forecast.dataset_notice}</p><p>Chỉ những tuần có đủ nhãn tương lai mới được dùng để tính tỷ lệ. Cần so sánh với baseline trước khi công bố ARIMA.</p></section> : <>
      <section className="analytics-section"><div className="section-heading"><div><p className="section-kicker">CHUỖI THỜI GIAN</p><h2>Quan sát và dự báo</h2></div><span>{forecast.unit === "week" ? "Theo tuần" : forecast.unit === "day" ? "Theo ngày" : "Chưa xác định đơn vị"} · {forecast.series_length ?? forecast.history.length} điểm quan sát</span></div><ForecastChart forecast={forecast} /><p className="source-note">{forecast.dataset_notice}</p></section>
      <section className="forecast-metrics" aria-label="Đánh giá mô hình dự báo"><div><span>Phương pháp</span><strong>{forecast.method === "Last mature value (naive)" ? "Giữ tỷ lệ chín gần nhất" : forecast.method ?? "Chưa công bố"}</strong></div><div><span>MAE</span><strong>{percentagePoints(forecast.mae)}</strong></div><div><span>RMSE</span><strong>{percentagePoints(forecast.rmse)}</strong></div><div><span>sMAPE</span><strong>{forecast.smape === null ? "Chưa có" : `${metric(forecast.smape)}%`}</strong></div></section>
      <section className="analytics-section"><p className="section-kicker">MỐC VÀ GIỚI HẠN</p><p>Đường quan sát và đường dự báo được vẽ riêng, không nối qua khoảng trống. Vạch dọc đánh dấu tuần chín nhãn cuối cùng. {forecast.method === "Last mature value (naive)" ? "Chuỗi ngắn nên chỉ dùng baseline đơn giản; không có khoảng tin cậy và không nên suy rộng dự báo xa." : "Dải khoảng tin cậy chỉ xuất hiện khi cả cận dưới và cận trên có cùng ngày."}</p></section>
    </>}
  </div></main>;
}
