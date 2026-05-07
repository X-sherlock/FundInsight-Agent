import { describe, expect, it } from "vitest";
import { chartHasData, getChartPoints } from "../../src/lib/chartSpec";
import type { ChartSpec } from "../../src/features/reports/types";

const chart: ChartSpec = {
  id: "returns_by_period",
  title: "多周期收益表现",
  type: "bar",
  description: "test chart",
  source_fields: ["metrics.performance.return_1y"],
  series: [{ name: "基金收益", values: [{ period: "1Y", value: 0.126 }] }],
  encoding: { x: "period", y: "value" },
  value_unit: "decimal_percent",
  notes: []
};

describe("chartSpec", () => {
  it("normalizes chart points from encoding metadata", () => {
    expect(chartHasData(chart)).toBe(true);
    expect(getChartPoints(chart)).toEqual([{ label: "1Y", value: 0.126, seriesName: "基金收益" }]);
  });

  it("detects charts without numeric values", () => {
    expect(chartHasData({ ...chart, series: [{ name: "empty", values: [{ period: "1Y", value: null }] }] })).toBe(
      false
    );
  });
});
