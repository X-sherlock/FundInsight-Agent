import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ChartRenderer } from "../../src/components/charts/ChartRenderer";
import { MarkdownReportViewer } from "../../src/components/markdown/MarkdownReportViewer";
import { QualityStatusBadge } from "../../src/components/status/QualityStatusBadge";
import { CoreConclusionPanel } from "../../src/features/reports/components/CoreConclusionPanel";
import { MetricCardGrid } from "../../src/features/reports/components/MetricCardGrid";
import { ReportGenerationTimeline } from "../../src/features/reports/components/ReportGenerationTimeline";
import { ResearchMaterialsPanel } from "../../src/features/reports/components/ResearchMaterialsPanel";
import { ResearchFusionPanel } from "../../src/features/reports/components/ResearchFusionPanel";
import { ChartGrid } from "../../src/components/charts/ChartGrid";
import type { ChartSpec, FactCard } from "../../src/features/reports/types";

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

  it("hides internal metric helper field names", () => {
    render(
      <MetricCardGrid
        metrics={[
          {
            label: "近一年收益",
            value: "15.80%",
            tone: "neutral",
            helper: "metrics.performance.return_1y"
          }
        ]}
      />
    );

    expect(screen.getByText("近一年收益")).toBeInTheDocument();
    expect(screen.queryByText("metrics.performance.return_1y")).not.toBeInTheDocument();
  });

  it("does not render chart source field details in chart cards", () => {
    const chart: ChartSpec = {
      id: "returns_by_period",
      title: "多周期收益表现",
      type: "bar",
      description: "展示收益。",
      source_fields: ["metrics.performance.return_1y"],
      series: [{ name: "基金收益", values: [{ period: "1Y", value: 0.158 }] }],
      encoding: { x: "period", y: "value" },
      value_unit: "decimal_percent",
      notes: []
    };
    render(<ChartGrid charts={[chart]} />);

    expect(screen.queryByText("来源字段")).not.toBeInTheDocument();
    expect(screen.queryByText("metrics.performance.return_1y")).not.toBeInTheDocument();
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
  it("hides research fusion when no signals are available", () => {
    const { container } = render(<ResearchFusionPanel context={null} />);
    expect(container).toBeEmptyDOMElement();
  });

  it("renders fact card chunks without pending sentiment or noisy web shell text", () => {
    const factCard: FactCard = {
      fund_code: "000001",
      source_metrics: {},
      derived_metrics: {},
      metric_tables: {},
      missing_fields: [],
      data_notes: [],
      limitations: [],
      retrieved_chunks: [
        {
          chunk_id: "mat_noisy_0000",
          material_id: "mat_noisy",
          fund_code: "000001",
          chunk_index: 0,
          evidence_text:
            "登录\n手机号\n获取验证码\n忘记密码\n立即注册\n扫码登录\n下载APP\n首页\n基金\n股票\n板块\n课程\nFund 000001 return text",
          relevance_score: 0.55,
          source_type: "news",
          title: "Noisy web page"
        },
        {
          chunk_id: "mat_clean_0000",
          material_id: "mat_clean",
          fund_code: "000001",
          chunk_index: 0,
          evidence_text: "Clean evidence about Fund 000001 drawdown and manager context.",
          relevance_score: 0.48,
          source_type: "report",
          title: "Clean research note",
          analysis_title: "历史收益与回撤背景",
          material_summary: "材料摘要说明基金收益和回撤背景。",
          sentiment_label: "positive",
          evidence_excerpt: "Clean evidence"
        }
      ],
      source_materials: []
    };

    render(<ResearchFusionPanel factCard={factCard} />);

    expect(screen.getByText("Clean research note")).toBeInTheDocument();
    expect(screen.getByText("历史收益与回撤背景")).toBeInTheDocument();
    expect(screen.getByText("材料摘要说明基金收益和回撤背景。")).toBeInTheDocument();
    expect(screen.getByText("正面")).toHaveClass("research-fusion__sentiment");
    expect(screen.getByText("Clean evidence")).toBeInTheDocument();
    expect(screen.getByText(/详细来源：标题《Clean research note》/)).toBeInTheDocument();
    expect(screen.getByText("证据原文")).toBeInTheDocument();
    expect(screen.queryByText("Noisy web page")).not.toBeInTheDocument();
    expect(screen.queryByText(/待模型解读/)).not.toBeInTheDocument();
  });

  it("sorts fact card chunks by relevance and hides overflow behind show more", () => {
    const factCard: FactCard = {
      fund_code: "000001",
      source_metrics: {},
      derived_metrics: {},
      metric_tables: {},
      missing_fields: [],
      data_notes: [],
      limitations: [],
      retrieved_chunks: [
        makeChunk("mat_low", "Low relevance", 0.12),
        makeChunk("mat_top", "Top relevance", 0.91),
        makeChunk("mat_second", "Second relevance", 0.82),
        makeChunk("mat_third", "Third relevance", 0.73),
        makeChunk("mat_fourth", "Fourth relevance", 0.64),
        makeChunk("mat_fifth", "Fifth relevance", 0.55)
      ],
      source_materials: []
    };

    const { container } = render(<ResearchFusionPanel factCard={factCard} />);
    const titles = [...container.querySelectorAll(".research-fusion__signal > strong")].map(
      (node) => node.textContent
    );

    expect(titles).toEqual(["Top relevance", "Second relevance", "Third relevance"]);
    expect(screen.queryByText("Low relevance")).not.toBeInTheDocument();
    expect(screen.queryByText("Fourth relevance")).not.toBeInTheDocument();
    expect(screen.queryByText("Fifth relevance")).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "展示更多（3）" }));
    expect(screen.getAllByText("Fourth relevance").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Fifth relevance").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Low relevance").length).toBeGreaterThan(0);
    expect(screen.getByRole("button", { name: "收起" })).toBeInTheDocument();
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
              source_url: "https://example.com/research-report",
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
    expect(screen.getByRole("link", { name: "虚构样例研报：科技主题基金关注因素梳理" })).toHaveAttribute(
      "href",
      "https://example.com/research-report"
    );
  });

  it("renders analyzed research materials when present", () => {
    render(
      <ResearchFusionPanel
        context={{
          fund_code: "005827",
          positive_factors: [
            {
              signal_id: "sig_positive",
              summary: "公开材料披露了基金一季度信息",
              confidence: 0.88,
              source_type: "report",
              evidence_text: "公开材料披露了基金一季度信息。"
            }
          ],
          risk_notices: [],
          key_events: [],
          view_changes: [],
          source_materials: [
            {
              material_id: "mat_quoted",
              fund_code: "005827",
              title: "实际引用材料",
              source_type: "report",
              source_name: "公开来源",
              publish_date: "2026-04-22",
              created_at: "2026-05-11T00:00:00+08:00"
            }
          ],
          analyzed_materials: [
            {
              material_id: "mat_1",
              title: "季度报告",
              source_type: "report",
              source_name: "基金公司",
              publish_date: "2026-04-22",
              signal_count: 1,
              chunk_count: 2
            },
            {
              material_id: "mat_2",
              title: "产品资料概要",
              source_type: "announcement",
              source_name: "基金公司",
              publish_date: "2026-04-20",
              signal_count: 0,
              chunk_count: 1
            }
          ],
          limitations: []
        }}
      />
    );

    expect(screen.getByText("本次纳入分析材料")).toBeInTheDocument();
    expect(screen.getByText("季度报告")).toBeInTheDocument();
    expect(screen.queryByText("产品资料概要")).not.toBeInTheDocument();
    expect(screen.queryByText("实际引用材料")).not.toBeInTheDocument();
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

  it("shows a friendly waiting prompt while uploading research material", async () => {
    render(
      <ResearchMaterialsPanel
        fund={{
          code: "WAIT01",
          name: "等待提示测试基金",
          type: "混合型",
          company: "测试基金公司",
          benchmark: "测试基准",
          category: "测试分类",
          asOfDate: "2026-05-14"
        }}
        includeResearch
        onIncludeResearchChange={() => undefined}
      />
    );

    const fileInput = document.querySelector<HTMLInputElement>("#research-file");
    expect(fileInput).not.toBeNull();

    const file = new File(["research material"], "等待提示材料.txt", { type: "text/plain" });
    fireEvent.change(fileInput as HTMLInputElement, { target: { files: [file] } });
    fireEvent.click(screen.getByRole("button", { name: "上传并入库" }));

    expect(screen.getByRole("status")).toHaveTextContent("正在上传并解析材料");
    expect(screen.getByRole("status")).toHaveTextContent("等待提示材料.txt");
    expect(screen.getByRole("button", { name: "正在入库..." })).toBeDisabled();

    await waitFor(() => {
      expect(screen.queryByRole("status")).not.toBeInTheDocument();
    });
  });
});

function makeChunk(chunkId: string, title: string, relevanceScore: number): FactCard["retrieved_chunks"][number] {
  return {
    chunk_id: chunkId,
    material_id: chunkId,
    fund_code: "000001",
    chunk_index: 0,
    evidence_text: `${title} evidence about Fund 000001 return and drawdown.`,
    relevance_score: relevanceScore,
    source_type: "report",
    title,
    analysis_title: `${title} 解读`,
    material_summary: `${title} summary.`,
    sentiment_label: "中性",
    evidence_excerpt: title
  };
}
