import { Activity, FileText, ShieldCheck, TriangleAlert } from "lucide-react";
import type { DashboardSummary } from "../reports/types";

export function DashboardOverview({ summary }: { summary: DashboardSummary }) {
  const cards = [
    { label: "报告总数", value: summary.total_reports, icon: FileText },
    { label: "检查通过", value: summary.passed_reports, icon: ShieldCheck },
    { label: "需复核", value: summary.warning_reports, icon: TriangleAlert },
    { label: "运行模式", value: summary.mock_mode ? "Mock" : "API", icon: Activity }
  ];

  return (
    <div className="overview-grid">
      {cards.map((card) => {
        const Icon = card.icon;
        return (
          <div className="metric-card" key={card.label}>
            <div className="metric-card__icon">
              <Icon size={18} />
            </div>
            <span>{card.label}</span>
            <strong>{card.value}</strong>
          </div>
        );
      })}
    </div>
  );
}
