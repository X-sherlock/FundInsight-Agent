import { ShieldCheck } from "lucide-react";
import type { GuardResult } from "../../features/reports/types";

export function GuardIssueList({ guardResult }: { guardResult: GuardResult }) {
  if (guardResult.passed) {
    return (
      <div className="guard-list guard-list--passed">
        <ShieldCheck size={18} />
        <span>报告结构与边界检查通过，未发现需要展示的 guard issue。</span>
      </div>
    );
  }

  return (
    <div className="guard-list">
      {guardResult.issues.map((issue) => (
        <div className="guard-list__item" key={`${issue.code}-${issue.message}`}>
          <strong>{issue.code}</strong>
          <span>{issue.message}</span>
        </div>
      ))}
    </div>
  );
}
