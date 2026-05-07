import { AlertTriangle } from "lucide-react";

export function RiskNoticePanel() {
  return (
    <div className="risk-notice">
      <AlertTriangle size={18} />
      <div>
        <strong>风险提示</strong>
        <p>本页面展示的是历史指标研究结果和 mock 报告样例，不构成任何投资建议。历史数据不代表后续结果。</p>
      </div>
    </div>
  );
}
