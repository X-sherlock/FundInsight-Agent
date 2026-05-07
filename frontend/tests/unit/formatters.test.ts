import { describe, expect, it } from "vitest";
import { formatChartValue, formatPercent } from "../../src/lib/formatters";

describe("formatters", () => {
  it("formats decimal percent values", () => {
    expect(formatPercent(0.126)).toBe("12.60%");
    expect(formatChartValue(-0.137, "decimal_percent")).toBe("-13.70%");
  });

  it("handles missing values", () => {
    expect(formatPercent(null)).toBe("缺失");
    expect(formatChartValue(undefined, "number")).toBe("缺失");
  });
});
