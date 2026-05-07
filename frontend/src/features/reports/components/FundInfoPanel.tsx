import type { ReportRecord } from "../types";

export function FundInfoPanel({ report }: { report: ReportRecord }) {
  const rows = [
    ["基金代码", report.fund.code],
    ["基金类型", report.fund.type],
    ["管理公司", report.fund.company],
    ["业绩基准", report.fund.benchmark],
    ["同类分类", report.fund.category],
    ["数据日期", report.as_of_date]
  ];

  return (
    <dl className="fund-info-panel">
      {rows.map(([label, value]) => (
        <div key={label}>
          <dt>{label}</dt>
          <dd>{value}</dd>
        </div>
      ))}
    </dl>
  );
}
