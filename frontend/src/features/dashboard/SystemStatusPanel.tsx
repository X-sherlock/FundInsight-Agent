import type { DashboardSummary } from "../reports/types";

export function SystemStatusPanel({ summary }: { summary: DashboardSummary }) {
  return (
    <div className="status-panel">
      {summary.system_status.map((item) => (
        <div className="status-panel__row" key={item.label}>
          <span>{item.label}</span>
          <strong className={`system-pill system-pill--${item.status}`}>{item.value}</strong>
        </div>
      ))}
    </div>
  );
}
