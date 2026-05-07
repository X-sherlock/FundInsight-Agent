import { Link } from "react-router-dom";
import type { ReportRecord } from "../reports/types";
import { formatDateTime } from "../../lib/formatters";
import { QualityStatusBadge } from "../../components/status/QualityStatusBadge";

export function RecentReportsTable({ reports }: { reports: ReportRecord[] }) {
  return (
    <div className="table-shell">
      <table>
        <thead>
          <tr>
            <th>报告</th>
            <th>基金代码</th>
            <th>数据日期</th>
            <th>创建时间</th>
            <th>状态</th>
          </tr>
        </thead>
        <tbody>
          {reports.map((report) => (
            <tr key={report.report_id}>
              <td>
                <Link to={`/reports/${report.report_id}`}>{report.fund.name}</Link>
              </td>
              <td>{report.fund.code}</td>
              <td>{report.as_of_date}</td>
              <td>{formatDateTime(report.created_at)}</td>
              <td>
                <QualityStatusBadge status={report.status} passed={report.guard_result.passed} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
