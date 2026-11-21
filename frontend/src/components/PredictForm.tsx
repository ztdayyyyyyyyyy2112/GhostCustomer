"use client";

import { useState, type FormEvent } from "react";
import { predict } from "@/lib/api";
import type { Customer, PredictResponse } from "@/types/api";

export function PredictForm({ examples }: { examples: Customer[] }) {
  const [customerId, setCustomerId] = useState(examples[0]?.customer_id ?? "");
  const [snapshotDate, setSnapshotDate] = useState(examples[0]?.snapshot_date ?? "");
  const [result, setResult] = useState<PredictResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  function selectCustomer(id: string) {
    setCustomerId(id);
    setResult(null);
    setError(null);
    const match = examples.find((item) => item.customer_id === id);
    if (match) setSnapshotDate(match.snapshot_date);
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPending(true);
    setResult(null);
    setError(null);
    try {
      const response = await predict({ customer_id: customerId.trim(), snapshot_date: snapshotDate });
      if (!Number.isFinite(response.score) || response.score < 0 || response.score > 1) {
        throw new Error("API trả về score ngoài khoảng [0, 1].");
      }
      setResult(response);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Không thể dự đoán. Vui lòng thử lại.");
    } finally {
      setPending(false);
    }
  }

  return (
    <div className="prediction-grid">
      <section className="analytics-section prediction-form-panel">
        <p className="section-kicker">THỬ LUỒNG DỰ ĐOÁN</p>
        <h2>Chọn snapshot</h2>
        <p>
          Form gửi mã khách hàng và ngày snapshot đến API; backend phải tạo đặc trưng chỉ từ sự kiện trước hoặc tại mốc T.
          Ở chế độ mock, kết quả chỉ kiểm tra giao diện.
        </p>
        <form onSubmit={submit} className="prediction-form" aria-label="Biểu mẫu thử nghiệm suy luận rủi ro">
          <label>
            Mã khách hàng
            <input
              required
              list="customer-options"
              value={customerId}
              onChange={(event) => selectCustomer(event.target.value)}
              placeholder="Nhập visitor ID (ví dụ: C001)"
              aria-label="Mã khách hàng cần dự đoán"
              aria-required="true"
            />
            <datalist id="customer-options">
              {examples.map((item) => (
                <option value={item.customer_id} key={item.customer_id} />
              ))}
            </datalist>
          </label>
          <label>
            Snapshot date
            <input
              required
              type="date"
              value={snapshotDate}
              onChange={(event) => {
                setSnapshotDate(event.target.value);
                setResult(null);
                setError(null);
              }}
              aria-label="Ngày snapshot T"
              aria-required="true"
            />
          </label>
          <button
            type="submit"
            className="primary-button"
            disabled={pending || !customerId.trim() || !snapshotDate}
            aria-busy={pending}
            aria-label={pending ? "Đang gọi API xử lý dự đoán" : "Gửi yêu cầu dự đoán"}
          >
            {pending ? "Đang gọi API…" : "Dự đoán"}
          </button>
        </form>
      </section>

      <section className="analytics-section prediction-result" aria-live="polite">
        <p className="section-kicker">KẾT QUẢ</p>
        {error ? (
          <div className="prediction-error" role="alert">
            <h2>Không có dự đoán</h2>
            <p>{error}</p>
          </div>
        ) : result ? (
          <div>
            <h2>{(result.score * 100).toFixed(1)}%</h2>
            <p className="result-caption">
              Xác suất ước lượng · {result.risk_label === "mock" ? "Nhãn minh họa" : result.risk_label}
            </p>
            <p className="source-note">{result.dataset_notice}</p>
            <p className="model-version">Model version: {result.model_version}</p>
            {result.top_factors.length > 0 ? (
              <div className="factors">
                <h3>Tín hiệu đóng góp</h3>
                <ul>
                  {result.top_factors.map((factor) => (
                    <li key={factor.feature}>
                      <span>{factor.feature}</span>
                      <strong>{factor.contribution.toFixed(3)}</strong>
                    </li>
                  ))}
                </ul>
                <p>Đây là đóng góp vào dự đoán, không phải quan hệ nhân quả.</p>
              </div>
            ) : (
              <p className="muted-text">Chưa có giải thích từ mô hình. Mock không tạo giá trị SHAP giả.</p>
            )}
          </div>
        ) : (
          <div className="prediction-placeholder">
            <h2>Chưa chạy dự đoán</h2>
            <p>Chọn mã khách hàng và snapshot để xem phản hồi từ API.</p>
          </div>
        )}
      </section>
    </div>
  );
}
