import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { createMemoryRouter, RouterProvider } from "react-router-dom";
import { describe, expect, it } from "vitest";
import { ReportCreatePage } from "../../src/pages/ReportCreatePage";
import { ReportDetailPage } from "../../src/pages/ReportDetailPage";
import { ReportTaskPage } from "../../src/pages/ReportTaskPage";

describe("report creation flow", () => {
  it("opens an existing report from the backend contract fallback", async () => {
    const router = createMemoryRouter(
      [
        { path: "/reports/new", element: <ReportCreatePage /> },
        { path: "/reports/tasks/:taskId", element: <ReportTaskPage /> },
        { path: "/reports/:reportId", element: <ReportDetailPage /> }
      ],
      { initialEntries: ["/reports/new"] }
    );

    render(<RouterProvider router={router} />);

    await screen.findByText("创建基金分析报告");
    await screen.findByText(/已读取 000001/);
    fireEvent.click(screen.getByText("查看或生成分析报告"));

    await waitFor(() => expect(screen.getByText("强制重新生成")).toBeInTheDocument(), {
      timeout: 2200
    });
    expect(screen.getByText("核心指标")).toBeInTheDocument();
  });
});
