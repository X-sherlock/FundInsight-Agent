import { ShieldAlert } from "lucide-react";

export function BoundaryNotice() {
  return (
    <div className="boundary-notice">
      <ShieldAlert size={18} />
      <div>
        <strong>研究边界</strong>
        <span>第三期仅展示历史指标解读和报告阅读体验，不提供行动建议，也不判断基金好坏。</span>
      </div>
    </div>
  );
}
