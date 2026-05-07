import type { ChartSpec, DataQuality } from "../types";

export function SourceFieldsDrawer({ charts, dataQuality }: { charts: ChartSpec[]; dataQuality: DataQuality }) {
  return (
    <details className="source-drawer">
      <summary>查看字段来源与数据局限</summary>
      <div className="source-drawer__content">
        <div>
          <h3>图表字段</h3>
          <ul>
            {charts.flatMap((chart) =>
              chart.source_fields.map((field) => (
                <li key={`${chart.id}-${field}`}>
                  <strong>{chart.title}</strong>
                  <span>{field}</span>
                </li>
              ))
            )}
          </ul>
        </div>
        <div>
          <h3>缺失字段</h3>
          <ul>
            {dataQuality.missing_fields.map((field) => (
              <li key={field}>{field}</li>
            ))}
          </ul>
        </div>
      </div>
    </details>
  );
}
