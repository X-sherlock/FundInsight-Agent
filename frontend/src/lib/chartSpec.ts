import type { ChartSpec } from "../features/reports/types";

export interface ChartPoint {
  label: string;
  value: number | null;
  seriesName: string;
}

export function chartHasData(chart: ChartSpec): boolean {
  return chart.series.some((series) =>
    series.values.some((point) =>
      Object.values(point).some((value) => typeof value === "number" && Number.isFinite(value))
    )
  );
}

export function getChartPoints(chart: ChartSpec): ChartPoint[] {
  const xKey = chart.encoding.x ?? chart.encoding.category;
  const yKey = chart.encoding.y ?? chart.encoding.value ?? "value";

  return chart.series.flatMap((series) =>
    series.values.map((point, index) => {
      const rawLabel = xKey ? point[xKey] : undefined;
      const rawValue = point[yKey];
      return {
        label: rawLabel === undefined || rawLabel === null ? `Item ${index + 1}` : String(rawLabel),
        value: typeof rawValue === "number" && Number.isFinite(rawValue) ? rawValue : null,
        seriesName: series.name
      };
    })
  );
}

export function getChartByPlaceholder(charts: ChartSpec[], placeholderId: string): ChartSpec | undefined {
  return charts.find((chart) => chart.id === placeholderId);
}
