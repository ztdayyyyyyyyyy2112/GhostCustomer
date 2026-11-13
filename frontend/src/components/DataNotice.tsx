import { isMockMode } from "@/lib/api";

export function DataNotice({ notice }: { notice?: string }) {
  return (
    <div className="notice" role="status">
      <strong>{notice ?? (isMockMode() ? "DỮ LIỆU MOCK MINH HỌA — không phải kết quả nghiên cứu" : "Chưa xác minh nguồn dữ liệu")}</strong>
      <span>“Ghost” là nhãn vận hành do nhóm định nghĩa; chưa phải bằng chứng khách hàng đã rời bỏ.</span>
    </div>
  );
}
