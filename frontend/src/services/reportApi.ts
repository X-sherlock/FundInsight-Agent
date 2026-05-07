import { mockDelay } from "./apiClient";
import { apiGet, apiPost } from "./httpClient";
import { mockFunds } from "../mocks/mockFunds";
import { buildDashboardSummary, mockReports } from "../mocks/mockReports";
import type {
  CreateReportRequest,
  CreateReportResponse,
  DashboardSummary,
  EnsureReportRequest,
  EnsureReportResponse,
  FundBrief,
  FundBriefApi,
  FundMetricsResponse,
  ReportRecord,
  ReportTaskStatus
} from "../features/reports/types";

interface FundSearchApiResponse {
  items: FundBriefApi[];
}

interface FundMetricsApiResponse {
  fund: FundBriefApi;
  metrics: Record<string, unknown>;
  raw: Record<string, unknown>;
}

interface ReportListApiResponse {
  items: ReportRecordApi[];
}

type ReportRecordApi = Omit<ReportRecord, "fund"> & {
  fund: FundBriefApi;
};

const USE_MOCK_API = import.meta.env.MODE === "test" || import.meta.env.VITE_USE_MOCK_API === "true";

export async function getDashboardSummary(): Promise<DashboardSummary> {
  if (USE_MOCK_API) {
    return mockDelay(buildDashboardSummary());
  }
  try {
    const summary = await apiGet<DashboardSummary>("/api/dashboard");
    return normalizeDashboardSummary(summary);
  } catch (issue) {
    if (isNetworkError(issue)) {
      return mockDelay(buildDashboardSummary());
    }
    throw issue;
  }
}

export async function searchFunds(query: string): Promise<FundBrief[]> {
  if (USE_MOCK_API) {
    return mockSearchFunds(query);
  }
  try {
    const response = await apiGet<FundSearchApiResponse>(`/api/funds?query=${encodeURIComponent(query)}`);
    return response.items.map(normalizeFundBrief);
  } catch (issue) {
    if (isNetworkError(issue)) {
      return mockSearchFunds(query);
    }
    throw issue;
  }
}

export async function getFundMetrics(fundCode: string): Promise<FundMetricsResponse> {
  if (USE_MOCK_API) {
    return mockFundMetrics(fundCode);
  }
  try {
    const response = await apiGet<FundMetricsApiResponse>(`/api/funds/${encodeURIComponent(fundCode)}/metrics`);
    return {
      fund: normalizeFundBrief(response.fund),
      metrics: response.metrics,
      raw: response.raw
    };
  } catch (issue) {
    if (isNetworkError(issue)) {
      return mockFundMetrics(fundCode);
    }
    throw issue;
  }
}

export async function ensureReport(request: EnsureReportRequest): Promise<EnsureReportResponse> {
  if (USE_MOCK_API) {
    return mockEnsureReport(request);
  }
  try {
    return await apiPost<EnsureReportResponse>("/api/reports/ensure", request);
  } catch (issue) {
    if (isNetworkError(issue)) {
      return mockEnsureReport(request);
    }
    throw issue;
  }
}

export async function createReport(request: CreateReportRequest): Promise<CreateReportResponse> {
  const response = await ensureReport({ fund_code: request.fund_code });
  return {
    report_id: response.report_id ?? response.task_id ?? `mock-report-${request.fund_code}`,
    status: "generating"
  };
}

export async function getReportTask(taskId: string): Promise<ReportTaskStatus> {
  if (USE_MOCK_API || taskId.startsWith("mock-task-")) {
    return mockReportTask(taskId);
  }
  return apiGet<ReportTaskStatus>(`/api/report-tasks/${encodeURIComponent(taskId)}`);
}

export async function getReport(reportId: string): Promise<ReportRecord> {
  if (USE_MOCK_API) {
    return mockReport(reportId);
  }
  try {
    const report = await apiGet<ReportRecordApi>(`/api/reports/${encodeURIComponent(reportId)}`);
    return normalizeReportRecord(report);
  } catch (issue) {
    if (isNetworkError(issue) || reportId.startsWith("mock-report-")) {
      return mockReport(reportId);
    }
    throw issue;
  }
}

export async function listReports(): Promise<ReportRecord[]> {
  if (USE_MOCK_API) {
    return mockDelay(mockReports);
  }
  try {
    const response = await apiGet<ReportListApiResponse>("/api/reports");
    return response.items.map(normalizeReportRecord);
  } catch (issue) {
    if (isNetworkError(issue)) {
      return mockDelay(mockReports);
    }
    throw issue;
  }
}

function normalizeDashboardSummary(summary: DashboardSummary): DashboardSummary {
  return {
    ...summary,
    latest_report: summary.latest_report
      ? normalizeReportRecord(summary.latest_report as unknown as ReportRecordApi)
      : undefined,
    recent_reports: summary.recent_reports.map((report) =>
      normalizeReportRecord(report as unknown as ReportRecordApi)
    )
  };
}

function normalizeReportRecord(report: ReportRecordApi): ReportRecord {
  return {
    ...report,
    fund: normalizeFundBrief(report.fund)
  };
}

function normalizeFundBrief(fund: FundBriefApi | FundBrief): FundBrief {
  if ("asOfDate" in fund) {
    return fund;
  }
  return {
    code: fund.code,
    name: fund.name,
    type: fund.type,
    company: fund.company,
    benchmark: fund.benchmark,
    asOfDate: fund.as_of_date,
    category: fund.category
  };
}

function isNetworkError(issue: unknown): boolean {
  return issue instanceof TypeError;
}

function mockSearchFunds(query: string): Promise<FundBrief[]> {
  const trimmed = query.trim().toLowerCase();
  const items = trimmed
    ? mockFunds.filter(
        (fund) =>
          fund.code.toLowerCase().includes(trimmed) ||
          fund.name.toLowerCase().includes(trimmed)
      )
    : mockFunds;
  return mockDelay(items);
}

function mockFundMetrics(fundCode: string): Promise<FundMetricsResponse> {
  const fund = mockFunds.find((item) => item.code === fundCode) ?? mockFunds[0];
  return mockDelay({ fund, metrics: {}, raw: {} });
}

function mockEnsureReport(request: EnsureReportRequest): Promise<EnsureReportResponse> {
  return mockDelay({
    mode: request.force_regenerate ? "created" : "existing",
    status: request.force_regenerate ? "queued" : "ready",
    report_id: request.force_regenerate ? null : `mock-report-${request.fund_code}`,
    task_id: request.force_regenerate ? `mock-task-${request.fund_code}` : null,
    report_url: request.force_regenerate ? null : `/api/reports/mock-report-${request.fund_code}`,
    status_url: request.force_regenerate ? `/api/report-tasks/mock-task-${request.fund_code}` : null
  });
}

function mockReportTask(taskId: string): Promise<ReportTaskStatus> {
  const fundCode = taskId.replace("mock-task-", "");
  return mockDelay({
    task_id: taskId,
    fund_code: fundCode,
    status: "completed",
    stage: "completed",
    stage_label: "报告已生成",
    message: "即将打开报告详情页。",
    report_id: `mock-report-${fundCode}`,
    error: null,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString()
  });
}

function mockReport(reportId: string): Promise<ReportRecord> {
  const normalizedId = reportId === "mock-report-000001" ? reportId : "mock-report-000001";
  const report = mockReports.find((item) => item.report_id === normalizedId);
  if (!report) {
    throw new Error("报告不存在。");
  }
  return mockDelay(report);
}
