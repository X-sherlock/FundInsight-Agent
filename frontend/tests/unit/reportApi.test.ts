import { describe, expect, it } from "vitest";
import {
  ensureReport,
  createResearchMaterial,
  deleteResearchMaterial,
  getDashboardSummary,
  getFundMetrics,
  getReport,
  getResearchContext,
  getReportTask,
  listResearchMaterials,
  searchFunds
} from "../../src/services/reportApi";

describe("report API service with mock fallback", () => {
  it("returns dashboard summary, sample funds, and local metrics preview", async () => {
    const summary = await getDashboardSummary();
    const funds = await searchFunds("000001");
    const metrics = await getFundMetrics("000001");

    expect(summary.recent_reports.length).toBeGreaterThanOrEqual(1);
    expect(funds[0].code).toBe("000001");
    expect(metrics.fund.code).toBe("000001");
  });

  it("ensures and loads a report through fallback contract", async () => {
    const ensured = await ensureReport({ fund_code: "000001" });
    const report = await getReport(ensured.report_id ?? "mock-report-000001");

    expect(ensured.mode).toBe("existing");
    expect(report.guard_result.passed).toBe(true);
    expect(report.chart_specs.charts.length).toBeGreaterThanOrEqual(5);
  });

  it("returns completed mock task for regeneration fallback", async () => {
    const ensured = await ensureReport({ fund_code: "000001", force_regenerate: true });
    const task = await getReportTask(ensured.task_id ?? "mock-task-000001");

    expect(ensured.mode).toBe("created");
    expect(task.status).toBe("completed");
    expect(task.report_id).toBe("mock-report-000001");
  });

  it("manages research materials and context through the typed API", async () => {
    const created = await createResearchMaterial("000001", {
      title: "research note",
      content: "research body",
      source_type: "report",
      source_name: "Research Desk",
      publish_date: "2026-05-01"
    });
    const materials = await listResearchMaterials("000001");
    const context = await getResearchContext("000001");
    const ensured = await ensureReport({ fund_code: "000001", include_research: true });

    expect(created.material_id).toContain("mock-material-000001");
    expect(materials.some((item) => item.material_id === created.material_id)).toBe(true);
    expect(context?.positive_factors ?? []).toEqual([]);
    expect(ensured.mode).toBe("created");

    await deleteResearchMaterial("000001", created.material_id);
    const afterDelete = await listResearchMaterials("000001");
    expect(afterDelete.some((item) => item.material_id === created.material_id)).toBe(false);
  });
});
