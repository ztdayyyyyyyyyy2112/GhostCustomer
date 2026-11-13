import { AppHeader } from "@/components/AppHeader";
import { DataNotice } from "@/components/DataNotice";
import { PredictForm } from "@/components/PredictForm";
import { getCustomers } from "@/lib/api";

export default async function PredictPage() {
  const { items, dataset_notice } = await getCustomers({ page: 1, page_size: 100 });
  return <main className="dashboard-shell"><AppHeader current="predict" /><div className="dashboard-content">
    <p className="eyebrow">SUY LUẬN / PREDICTION</p>
    <div className="title-row"><div><h1>Thử dự đoán</h1><p className="subtitle">Gửi một snapshot đến API và xem score, nhãn rủi ro cùng tín hiệu giải thích khi mô hình sẵn sàng.</p></div></div>
    <DataNotice notice={dataset_notice} />
    <PredictForm examples={items} />
  </div></main>;
}
