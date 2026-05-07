import { createBrowserRouter, Navigate } from "react-router-dom";
import { AppShell } from "../layouts/AppShell";
import { DashboardPage } from "../pages/DashboardPage";
import { PlaceholderPage } from "../pages/PlaceholderPage";
import { ReportCreatePage } from "../pages/ReportCreatePage";
import { ReportDetailPage } from "../pages/ReportDetailPage";
import { ReportTaskPage } from "../pages/ReportTaskPage";

export const router = createBrowserRouter([
  {
    element: <AppShell />,
    children: [
      { path: "/", element: <Navigate to="/dashboard" replace /> },
      { path: "/dashboard", element: <DashboardPage /> },
      { path: "/reports/new", element: <ReportCreatePage /> },
      { path: "/reports/tasks/:taskId", element: <ReportTaskPage /> },
      { path: "/reports/:reportId", element: <ReportDetailPage /> },
      {
        path: "/reports/history",
        element: (
          <PlaceholderPage
            title="历史报告管理"
            description="这里将用于检索、筛选和复核历史报告。第三期保留产品入口。"
          />
        )
      },
      {
        path: "/funds",
        element: (
          <PlaceholderPage
            title="基金指标展示"
            description="这里将展示基金指标、数据质量和指标口径说明。第三期保留模块空间。"
          />
        )
      },
      {
        path: "/compare",
        element: (
          <PlaceholderPage
            title="基金对比"
            description="这里将支持多基金横向研究。第三期仅预留导航与布局。"
          />
        )
      },
      {
        path: "/batch",
        element: (
          <PlaceholderPage
            title="批量分析"
            description="这里将支持批量任务、进度追踪和结果复核。第三期仅预留入口。"
          />
        )
      },
      {
        path: "/settings",
        element: (
          <PlaceholderPage
            title="系统设置"
            description="这里将管理模型提供方、数据源和报告模板信息。第三期展示系统骨架。"
          />
        )
      }
    ]
  }
]);
