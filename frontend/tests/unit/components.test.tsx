import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ChartRenderer } from "../../src/components/charts/ChartRenderer";
import { MarkdownReportViewer } from "../../src/components/markdown/MarkdownReportViewer";
import { QualityStatusBadge } from "../../src/components/status/QualityStatusBadge";
import type { ChartSpec } from "../../src/features/reports/types";

describe("frontend components", () => {
  it("renders report quality status", () => {
    render(<QualityStatusBadge status="passed" passed />);
    expect(screen.getByLabelText("Report status Passed")).toBeInTheDocument();
  });

  it("renders chart empty state for missing values", () => {
    const chart: ChartSpec = {
      id: "empty_chart",
      title: "空图表",
      type: "bar",
      description: "No values",
      source_fields: ["metrics.empty"],
      series: [{ name: "empty", values: [{ metric: "A", value: null }] }],
      encoding: { x: "metric", y: "value" },
      value_unit: "number",
      notes: []
    };
    render(<ChartRenderer chart={chart} />);
    expect(screen.getByText("暂无可渲染数据")).toBeInTheDocument();
  });

  it("does not render markdown chart comments as visible placeholders", () => {
    render(<MarkdownReportViewer markdown={"# 示例分析报告\n\n<!-- chart: returns_by_period -->\n\n正文"} charts={[]} />);
    expect(screen.queryByText("图表占位")).not.toBeInTheDocument();
    expect(screen.getByText("正文")).toBeInTheDocument();
  });

  it("can hide the first markdown title when the page already renders it", () => {
    render(<MarkdownReportViewer markdown={"# 示例分析报告\n\n## 报告说明\n\n正文"} charts={[]} hideTitle />);
    expect(screen.queryByText("示例分析报告")).not.toBeInTheDocument();
    expect(screen.getByText("报告说明")).toBeInTheDocument();
  });
});
