import type { KeyMetric } from "../types";

export function MetricCardGrid({ metrics }: { metrics: KeyMetric[] }) {
  return (
    <div className="metric-card-grid">
      {metrics.map((metric) => (
        <div className={`metric-card metric-card--${metric.tone ?? "neutral"}`} key={metric.label}>
          <span>{metric.label}</span>
          <strong>{metric.value}</strong>
        </div>
      ))}
    </div>
  );
}
