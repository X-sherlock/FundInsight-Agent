import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Card } from "../components/ui/Card";
import { BoundaryNotice } from "../features/reports/components/BoundaryNotice";
import { FundPreviewCard } from "../features/reports/components/FundPreviewCard";
import { FundSearchBox } from "../features/reports/components/FundSearchBox";
import { ReportCreateForm } from "../features/reports/components/ReportCreateForm";
import { ResearchMaterialsPanel } from "../features/reports/components/ResearchMaterialsPanel";
import type { FundBrief, FundMetricsResponse } from "../features/reports/types";
import { ensureReport, getFundMetrics, searchFunds } from "../services/reportApi";

export function ReportCreatePage() {
  const navigate = useNavigate();
  const [query, setQuery] = useState("000001");
  const [funds, setFunds] = useState<FundBrief[]>([]);
  const [selectedFund, setSelectedFund] = useState<FundBrief | undefined>();
  const [fundMetrics, setFundMetrics] = useState<FundMetricsResponse | null>(null);
  const [metricsLoading, setMetricsLoading] = useState(false);
  const [loading, setLoading] = useState(false);
  const [includeResearch, setIncludeResearch] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    searchFunds(query)
      .then((items) => {
        if (!mounted) {
          return;
        }
        setFunds(items);
        setSelectedFund((current) =>
          current && items.some((item) => item.code === current.code) ? current : items[0]
        );
      })
      .catch((issue) => {
        if (mounted) {
          setError(issue instanceof Error ? issue.message : "基金查询失败。");
        }
      });
    return () => {
      mounted = false;
    };
  }, [query]);

  useEffect(() => {
    let mounted = true;
    if (!selectedFund) {
      setFundMetrics(null);
      return;
    }
    setMetricsLoading(true);
    getFundMetrics(selectedFund.code)
      .then((data) => {
        if (mounted) {
          setFundMetrics(data);
        }
      })
      .catch((issue) => {
        if (mounted) {
          setFundMetrics(null);
          setError(issue instanceof Error ? issue.message : "基金指标加载失败。");
        }
      })
      .finally(() => {
        if (mounted) {
          setMetricsLoading(false);
        }
      });
    return () => {
      mounted = false;
    };
  }, [selectedFund]);

  const metricsStatus = useMemo(() => {
    if (metricsLoading) {
      return "正在读取后端基金指标...";
    }
    if (fundMetrics) {
      return `已读取 ${fundMetrics.fund.code} 的结构化指标数据，数据日期 ${fundMetrics.fund.asOfDate}。`;
    }
    return "请选择基金以读取后端指标。";
  }, [fundMetrics, metricsLoading]);

  async function handleCreate() {
    if (!selectedFund) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await ensureReport({
        fund_code: selectedFund.code,
        include_research: includeResearch
      });
      if (response.mode === "existing" && response.report_id) {
        navigate(`/reports/${response.report_id}`);
        return;
      }
      if (response.task_id) {
        navigate(`/reports/tasks/${response.task_id}`);
        return;
      }
      throw new Error("报告请求未返回可打开的报告或任务。");
    } catch (issue) {
      setError(issue instanceof Error ? issue.message : "报告请求失败。");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="page-stack">
      <section className="page-heading">
        <p className="eyebrow">Report Creation</p>
        <h1>创建基金分析报告</h1>
        <p>选择基金代码后读取后端本地指标数据；已有报告会直接打开，无报告时创建异步生成任务。</p>
      </section>

      <BoundaryNotice />

      <div className="create-grid">
        <Card title="选择基金" eyebrow="Input">
          <FundSearchBox
            query={query}
            funds={funds}
            selectedCode={selectedFund?.code}
            onQueryChange={setQuery}
            onSelect={setSelectedFund}
          />
        </Card>

        <Card title="报告参数" eyebrow="Generation">
          <FundPreviewCard fund={selectedFund} />
          <div className="data-source-summary">{metricsStatus}</div>
          <ReportCreateForm fund={selectedFund} loading={loading} onSubmit={handleCreate} />
          {error && <div className="form-error">{error}</div>}
        </Card>
      </div>

      <Card title="投研材料" eyebrow="Research">
        <ResearchMaterialsPanel
          fund={selectedFund}
          includeResearch={includeResearch}
          onIncludeResearchChange={setIncludeResearch}
        />
      </Card>
    </div>
  );
}
