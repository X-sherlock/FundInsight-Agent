import type { ChartSpec } from "../../features/reports/types";
import { ChartRenderer } from "./ChartRenderer";

export function ChartGrid({ charts }: { charts: ChartSpec[] }) {
  return (
    <div className="chart-grid">
      {charts.map((chart) => (
        <article className="chart-card" key={chart.id}>
          <div className="chart-card__header">
            <div>
              <h3>{chart.title}</h3>
              <p>{chart.description}</p>
            </div>
            <span>{chart.type}</span>
          </div>
          <ChartRenderer chart={chart} />
          <details className="source-fields">
            <summary>来源字段</summary>
            <ul>
              {chart.source_fields.map((field) => (
                <li key={field}>{field}</li>
              ))}
            </ul>
          </details>
        </article>
      ))}
    </div>
  );
}
