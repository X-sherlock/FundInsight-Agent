import { FileText } from "lucide-react";
import type { FormEvent } from "react";
import { Button } from "../../../components/ui/Button";
import type { FundBrief } from "../types";

interface ReportCreateFormProps {
  fund?: FundBrief;
  loading: boolean;
  onSubmit: () => void;
}

export function ReportCreateForm({ fund, loading, onSubmit }: ReportCreateFormProps) {
  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    onSubmit();
  }

  return (
    <form className="report-create-form" data-testid="report-create-form" onSubmit={handleSubmit}>
      <div>
        <label>数据来源</label>
        <select value="backend-local" disabled>
          <option value="backend-local">后端本地结构化指标</option>
        </select>
      </div>
      <div>
        <label>报告策略</label>
        <select value="ensure" disabled>
          <option value="ensure">已有报告直接打开，无报告则生成</option>
        </select>
      </div>
      <Button type="submit" disabled={!fund || loading}>
        <FileText size={17} />
        查看或生成分析报告
      </Button>
    </form>
  );
}
