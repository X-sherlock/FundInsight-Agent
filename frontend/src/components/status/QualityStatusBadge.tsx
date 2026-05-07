import { AlertTriangle, CheckCircle2, Clock, XCircle } from "lucide-react";
import type { ReportStatus } from "../../features/reports/types";

interface QualityStatusBadgeProps {
  status: ReportStatus;
  passed?: boolean;
}

const statusMap = {
  generating: { label: "Generating", icon: Clock, className: "status-badge--mock" },
  passed: { label: "Passed", icon: CheckCircle2, className: "status-badge--ok" },
  warning: { label: "Warning", icon: AlertTriangle, className: "status-badge--warning" },
  failed: { label: "Failed", icon: XCircle, className: "status-badge--danger" }
};

export function QualityStatusBadge({ status, passed }: QualityStatusBadgeProps) {
  const resolvedStatus = passed === false && status === "passed" ? "warning" : status;
  const item = statusMap[resolvedStatus];
  const Icon = item.icon;
  return (
    <span className={`status-badge ${item.className}`} aria-label={`Report status ${item.label}`}>
      <Icon size={14} />
      {item.label}
    </span>
  );
}
