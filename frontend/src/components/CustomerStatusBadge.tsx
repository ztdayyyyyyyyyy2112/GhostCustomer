import type { CustomerStatus } from "@/types/api";

export const statusLabels: Record<CustomerStatus, string> = {
  active: "Đang hoạt động",
  ghost: "Ghost",
  candidate: "Cần theo dõi",
  recovered: "Hoạt động lại",
  inactive: "Ngừng hoạt động",
  unknown: "Chưa xác định",
};

export function CustomerStatusBadge({ status }: { status: CustomerStatus }) {
  return <span className={`status-badge status-${status}`}>{statusLabels[status]}</span>;
}
