import { isMockMode } from "@/lib/api";

export function DataNotice() {
  return (
    <div className="notice" role="status">
      {isMockMode() && <strong>DỮ LIỆU MOCK MINH HỌA — không phải kết quả nghiên cứu</strong>}
      <span>“Ghost” là nhãn vận hành do nhóm định nghĩa; chưa phải bằng chứng khách hàng đã rời bỏ.</span>
    </div>
  );
}
