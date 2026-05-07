import { chartHasData, getChartPoints } from "../../lib/chartSpec";
import { formatChartValue } from "../../lib/formatters";
import type { ChartSpec } from "../../features/reports/types";

const pieColors = ["#0f766e", "#2563eb", "#b45309", "#64748b", "#7c3aed"];

export function ChartRenderer({ chart }: { chart: ChartSpec }) {
  if (!chartHasData(chart)) {
    return (
      <div className="chart-empty">
        <strong>暂无可渲染数据</strong>
        <span>该图表的 series 中没有非空数值。</span>
      </div>
    );
  }

  if (chart.type === "pie") {
    return <PieChart chart={chart} />;
  }
  if (chart.type === "line") {
    return <LinePlaceholder chart={chart} />;
  }
  return <BarChart chart={chart} />;
}

function BarChart({ chart }: { chart: ChartSpec }) {
  const points = getChartPoints(chart);
  const max = Math.max(...points.map((point) => Math.abs(point.value ?? 0)), 0.01);

  return (
    <div className="bar-chart" role="img" aria-label={chart.title}>
      {points.map((point) => {
        const width = point.value === null ? 0 : Math.max(8, (Math.abs(point.value) / max) * 100);
        return (
          <div className="bar-chart__row" key={`${point.seriesName}-${point.label}`}>
            <span className="bar-chart__label">{point.label}</span>
            <div className="bar-chart__track">
              <span
                className={point.value !== null && point.value < 0 ? "bar-chart__bar is-negative" : "bar-chart__bar"}
                style={{ width: `${width}%` }}
              />
            </div>
            <span className="bar-chart__value">{formatChartValue(point.value, chart.value_unit)}</span>
          </div>
        );
      })}
    </div>
  );
}

function PieChart({ chart }: { chart: ChartSpec }) {
  const points = getChartPoints(chart).filter((point) => point.value !== null && point.value > 0);
  const total = points.reduce((sum, point) => sum + (point.value ?? 0), 0);
  let cumulative = 0;

  return (
    <div className="pie-chart" role="img" aria-label={chart.title}>
      <svg viewBox="0 0 42 42" className="pie-chart__svg" aria-hidden="true">
        <circle cx="21" cy="21" r="15.915" fill="transparent" stroke="#e2e8f0" strokeWidth="6" />
        {points.map((point, index) => {
          const value = point.value ?? 0;
          const portion = value / total;
          const dashArray = `${portion * 100} ${100 - portion * 100}`;
          const dashOffset = 25 - cumulative * 100;
          cumulative += portion;
          return (
            <circle
              key={point.label}
              cx="21"
              cy="21"
              r="15.915"
              fill="transparent"
              stroke={pieColors[index % pieColors.length]}
              strokeWidth="6"
              strokeDasharray={dashArray}
              strokeDashoffset={dashOffset}
            />
          );
        })}
      </svg>
      <div className="pie-chart__legend">
        {points.map((point, index) => (
          <div className="pie-chart__legend-item" key={point.label}>
            <span style={{ background: pieColors[index % pieColors.length] }} />
            <strong>{point.label}</strong>
            <em>{formatChartValue(point.value, chart.value_unit)}</em>
          </div>
        ))}
      </div>
    </div>
  );
}

function LinePlaceholder({ chart }: { chart: ChartSpec }) {
  return (
    <div className="chart-empty">
      <strong>{chart.title}</strong>
      <span>Line chart renderer is reserved for later time-series data.</span>
    </div>
  );
}
