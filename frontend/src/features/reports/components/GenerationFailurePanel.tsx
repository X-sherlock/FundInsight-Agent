import { RotateCcw, Search } from "lucide-react";
import { Link } from "react-router-dom";
import { Button } from "../../../components/ui/Button";
import type { ReportTaskStatus } from "../types";

interface GenerationFailurePanelProps {
  task: ReportTaskStatus;
  retrying: boolean;
  onRetry: () => void;
}

export function GenerationFailurePanel({ task, retrying, onRetry }: GenerationFailurePanelProps) {
  return (
    <div className="generation-failure" role="alert">
      <div>
        <p className="eyebrow">Generation Failed</p>
        <h2>报告生成未完成</h2>
        <p>{task.error?.message ?? task.message}</p>
        {task.error?.code && <span>错误码：{task.error.code}</span>}
      </div>
      <div className="generation-failure__actions">
        <Button type="button" disabled={retrying} onClick={onRetry}>
          <RotateCcw size={17} />
          重试或打开已有报告
        </Button>
        <Link className="button button--secondary" to="/reports/new">
          <Search size={17} />
          返回基金选择
        </Link>
      </div>
    </div>
  );
}
