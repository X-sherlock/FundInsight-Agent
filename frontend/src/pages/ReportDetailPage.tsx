import { RefreshCw } from "lucide-react";
import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { ChartGrid } from "../components/charts/ChartGrid";
import { MarkdownReportViewer } from "../components/markdown/MarkdownReportViewer";
import { GuardIssueList } from "../components/status/GuardIssueList";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { CoreConclusionPanel } from "../features/reports/components/CoreConclusionPanel";
import { FundInfoPanel } from "../features/reports/components/FundInfoPanel";
import { MetricCardGrid } from "../features/reports/components/MetricCardGrid";
import { ReportHeader } from "../features/reports/components/ReportHeader";
import { RiskNoticePanel } from "../features/reports/components/RiskNoticePanel";
import { SourceFieldsDrawer } from "../features/reports/components/SourceFieldsDrawer";
import type { ReportRecord } from "../features/reports/types";
import { extractMarkdownTitle } from "../lib/markdownSections";
import { ensureReport, getReport } from "../services/reportApi";

export function ReportDetailPage() {
  const { reportId } = useParams();
  const navigate = useNavigate();
  const [report, setReport] = useState<ReportRecord | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [regenerating, setRegenerating] = useState(false);

  useEffect(() => {
    let mounted = true;
    if (!reportId) {
      setError("缺少报告 ID。");
      return;
    }
    getReport(reportId)
      .then((data) => {
        if (mounted) {
          setReport(data);
        }
      })
      .catch((issue) => {
        if (mounted) {
          setError(issue instanceof Error ? issue.message : "报告加载失败。");
        }
      });
    return () => {
      mounted = false;
    };
  }, [reportId]);

  async function handleRegenerate() {
    if (!report) {
      return;
    }
    setRegenerating(true);
    setError(null);
    try {
      const response = await ensureReport({ fund_code: report.fund.code, force_regenerate: true });
      if (response.task_id) {
        navigate(`/reports/tasks/${response.task_id}`);
      } else if (response.report_id) {
        navigate(`/reports/${response.report_id}`);
      }
    } catch (issue) {
      setError(issue instanceof Error ? issue.message : "重新生成请求失败。");
    } finally {
      setRegenerating(false);
    }
  }

  if (error) {
    return <div className="page-error">{error}</div>;
  }

  if (!report) {
    return <div className="page-loading">正在加载报告详情...</div>;
  }

  return (
    <div className="page-stack">
      <ReportHeader report={report} />
      <div className="report-actions">
        <Button type="button" variant="secondary" disabled={regenerating} onClick={handleRegenerate}>
          <RefreshCw size={17} />
          强制重新生成
        </Button>
      </div>
      <RiskNoticePanel />

      <div className="report-layout">
        <div className="report-layout__main">
          <Card title="核心结论" eyebrow="Summary">
            <CoreConclusionPanel conclusions={report.core_conclusions} />
          </Card>

          <Card title="核心指标" eyebrow="Metrics">
            <MetricCardGrid metrics={report.key_metrics} />
          </Card>

          <Card title="图表区域" eyebrow="Chart Specs">
            <ChartGrid charts={report.chart_specs.charts} />
          </Card>

          <Card title={extractMarkdownTitle(report.markdown)} eyebrow="Report Body">
            <MarkdownReportViewer markdown={report.markdown} charts={report.chart_specs.charts} hideTitle />
          </Card>
        </div>

        <aside className="report-layout__side">
          <Card title="基金基本信息" eyebrow="Fund">
            <FundInfoPanel report={report} />
          </Card>
          <Card title="报告质量状态" eyebrow="Guard">
            <GuardIssueList guardResult={report.guard_result} />
          </Card>
          <Card title="数据质量" eyebrow="Source">
            <SourceFieldsDrawer charts={report.chart_specs.charts} dataQuality={report.data_quality} />
          </Card>
        </aside>
      </div>
    </div>
  );
}
