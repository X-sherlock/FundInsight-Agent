import { FileClock, FilePlus2 } from "lucide-react";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Card } from "../components/ui/Card";
import { DashboardOverview } from "../features/dashboard/DashboardOverview";
import { FeatureEntryCard } from "../features/dashboard/FeatureEntryCard";
import { FutureModuleGrid } from "../features/dashboard/FutureModuleGrid";
import { RecentReportsTable } from "../features/dashboard/RecentReportsTable";
import { SystemStatusPanel } from "../features/dashboard/SystemStatusPanel";
import type { DashboardSummary } from "../features/reports/types";
import { getDashboardSummary } from "../services/reportApi";

export function DashboardPage() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);

  useEffect(() => {
    let mounted = true;
    getDashboardSummary().then((data) => {
      if (mounted) {
        setSummary(data);
      }
    });
    return () => {
      mounted = false;
    };
  }, []);

  if (!summary) {
    return <div className="page-loading">正在加载 Dashboard...</div>;
  }

  return (
    <div className="page-stack">
      <section className="dashboard-hero">
        <div>
          <p className="eyebrow">Phase 3 Frontend</p>
          <h1>基金研究与报告管理系统</h1>
          <p>
            以 Dashboard 为系统入口，保留报告生成、指标展示、对比分析、批量任务和历史管理的产品结构。
          </p>
        </div>
        <Link className="button button--primary" to="/reports/new">
          <FilePlus2 size={17} />
          生成分析报告
        </Link>
      </section>

      <DashboardOverview summary={summary} />

      <div className="dashboard-grid">
        <Card title="核心功能入口" eyebrow="Workspace">
          <div className="feature-grid">
            <FeatureEntryCard
              title="生成分析报告"
              description="选择样本基金并进入 mock 报告生成流程。"
              to="/reports/new"
              icon={FilePlus2}
              active
            />
            <FeatureEntryCard
              title="历史报告管理"
              description="预留报告检索、复核和再生成入口。"
              to="/reports/history"
              icon={FileClock}
            />
          </div>
        </Card>
        <Card title="系统状态" eyebrow="Runtime">
          <SystemStatusPanel summary={summary} />
        </Card>
      </div>

      <Card title="未来模块" eyebrow="Roadmap">
        <FutureModuleGrid />
      </Card>

      <Card title="最近报告" eyebrow="Reports">
        <RecentReportsTable reports={summary.recent_reports} />
      </Card>
    </div>
  );
}
