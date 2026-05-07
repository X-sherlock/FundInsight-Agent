import { CalendarDays } from "lucide-react";
import { QualityStatusBadge } from "../../../components/status/QualityStatusBadge";
import type { ReportRecord } from "../types";

export function ReportHeader({ report }: { report: ReportRecord }) {
  return (
    <section className="report-header">
      <div>
        <p className="eyebrow">Fund Analysis Report</p>
        <h1>{report.fund.name}</h1>
        <div className="report-header__meta">
          <span>{report.fund.code}</span>
          <span>{report.fund.type}</span>
          <span>
            <CalendarDays size={15} />
            {report.as_of_date}
          </span>
        </div>
      </div>
      <QualityStatusBadge status={report.status} passed={report.guard_result.passed} />
    </section>
  );
}
