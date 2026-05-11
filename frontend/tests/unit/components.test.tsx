import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ChartRenderer } from "../../src/components/charts/ChartRenderer";
import { MarkdownReportViewer } from "../../src/components/markdown/MarkdownReportViewer";
import { QualityStatusBadge } from "../../src/components/status/QualityStatusBadge";
import { CoreConclusionPanel } from "../../src/features/reports/components/CoreConclusionPanel";
import { ReportGenerationTimeline } from "../../src/features/reports/components/ReportGenerationTimeline";
import { ResearchFusionPanel } from "../../src/features/reports/components/ResearchFusionPanel";
import type { ChartSpec } from "../../src/features/reports/types";

describe("frontend components", () => {
  it("renders report quality status", () => {
    render(<QualityStatusBadge status="passed" passed />);
    expect(screen.getByLabelText("Report status Passed")).toBeInTheDocument();
  });

  it("renders inline bold markdown in core conclusions", () => {
    render(<CoreConclusionPanel conclusions={["**收益质量**需要结合波动率观察。", "*风险控制**需要结合回撤观察。"]} />);

    expect(screen.getByText("收益质量").tagName).toBe("STRONG");
    expect(screen.getByText("风险控制").tagName).toBe("STRONG");
    expect(screen.queryByText("**收益质量**需要结合波动率观察。")).not.toBeInTheDocument();
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
  it("renders research fusion empty state without crashing", () => {
    render(<ResearchFusionPanel context={null} />);
    expect(screen.getByText("暂无投研材料融合信息")).toBeInTheDocument();
  });

  it("renders research fusion signals and source materials", () => {
    render(
      <ResearchFusionPanel
        context={{
          fund_code: "000005",
          positive_factors: [
            {
              signal_id: "sig_positive",
              summary: "研报样例关注近一年相对基准表现",
              confidence: 0.88,
              importance: "high",
              source_type: "report",
              evidence_text: "虚构研报样例将该基金列为科技主题观察名单。"
            }
          ],
          risk_notices: [
            {
              signal_id: "sig_risk",
              summary: "新闻样例提示科技板块估值波动",
              confidence: 0.84,
              source_type: "news",
              evidence_text: "虚构新闻样例称，近期科技板块估值波动。"
            }
          ],
          key_events: [
            {
              signal_id: "sig_event",
              summary: "公告样例披露投资范围未变化",
              confidence: 0.86,
              source_type: "announcement",
              evidence_text: "虚构公告样例披露，基金合同中的投资范围未变化。"
            }
          ],
          view_changes: [
            {
              signal_id: "sig_view",
              summary: "内部投研材料提到跟踪框架变化",
              confidence: 0.82,
              source_type: "internal_research",
              evidence_text: "团队将观点从单一成长弹性关注调整为多维观察。"
            }
          ],
          source_materials: [
            {
              material_id: "mat_1",
              fund_code: "000005",
              title: "虚构样例研报：科技主题基金关注因素梳理",
              source_type: "report",
              source_name: "虚构研报样例",
              publish_date: "2026-04-08",
              created_at: "2026-05-11T00:00:00+08:00"
            }
          ],
          limitations: []
        }}
      />
    );

    expect(screen.getByText("研报样例关注近一年相对基准表现")).toBeInTheDocument();
    expect(screen.getByText("新闻样例提示科技板块估值波动")).toBeInTheDocument();
    expect(screen.getByText("公告样例披露投资范围未变化")).toBeInTheDocument();
    expect(screen.getByText("内部投研材料提到跟踪框架变化")).toBeInTheDocument();
    expect(screen.getByText("虚构样例研报：科技主题基金关注因素梳理")).toBeInTheDocument();
  });

  it("renders research task stages", () => {
    render(
      <ReportGenerationTimeline
        task={{
          task_id: "task_1",
          fund_code: "000001",
          status: "extracting_research",
          stage: "extracting_research",
          stage_label: "正在抽取投研材料",
          message: "正在从已保存的投研材料中抽取结构化信号。",
          report_id: null,
          error: null,
          created_at: "2026-05-09T00:00:00+08:00",
          updated_at: "2026-05-09T00:00:00+08:00"
        }}
      />
    );
    expect(screen.getByText("正在抽取投研材料")).toBeInTheDocument();
  });

  it("renders research fusion task stage", () => {
    render(
      <ReportGenerationTimeline
        task={{
          task_id: "task_2",
          fund_code: "000005",
          status: "fusing_research",
          stage: "fusing_research",
          stage_label: "正在融合投研信息",
          message: "正在整理投研材料信号，生成报告可用的融合上下文。",
          report_id: null,
          error: null,
          created_at: "2026-05-09T00:00:00+08:00",
          updated_at: "2026-05-09T00:00:00+08:00"
        }}
      />
    );
    expect(screen.getByText("正在融合投研信息")).toBeInTheDocument();
  });
});
