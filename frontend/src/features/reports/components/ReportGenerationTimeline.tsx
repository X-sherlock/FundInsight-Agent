import { CheckCircle2, Circle, Loader2, XCircle } from "lucide-react";
import type { ReportTaskStage, ReportTaskStatus } from "../types";

const stages: Array<{ stage: ReportTaskStage; label: string; message: string }> = [
  { stage: "queued", label: "已加入报告生成队列", message: "系统正在准备处理该基金的报告请求。" },
  { stage: "loading_data", label: "正在读取基金指标", message: "正在加载后端保存的基金基础信息、收益、风险、持仓和数据质量字段。" },
  { stage: "planning_context", label: "正在整理分析上下文", message: "正在组织指标表格、缺失字段、图表草案和可解释的分析线索。" },
  { stage: "llm_generating", label: "正在生成分析报告", message: "模型正在基于结构化指标生成非投顾性质的 Markdown 分析内容。" },
  { stage: "parsing_charts", label: "正在解析图表信息", message: "正在提取报告正文中的图表占位和对应 chart specs。" },
  { stage: "quality_checking", label: "正在进行质量检查", message: "正在检查必需章节、图表一致性和明显边界风险。" },
  { stage: "saving_report", label: "正在保存报告", message: "正在写入报告正文、图表规格和生成元数据。" },
  { stage: "completed", label: "报告已生成", message: "即将打开报告详情页。" }
];

export function ReportGenerationTimeline({ task }: { task: ReportTaskStatus }) {
  const currentIndex = stages.findIndex((item) => item.stage === task.stage);
  return (
    <div className="generation-timeline" aria-label="报告生成阶段">
      {stages.map((item, index) => {
        const isCurrent = item.stage === task.stage;
        const isDone = task.status === "completed" || (currentIndex >= 0 && index < currentIndex);
        const isFailed = task.status === "failed" && isCurrent;
        const Icon = isFailed ? XCircle : isDone ? CheckCircle2 : isCurrent ? Loader2 : Circle;
        return (
          <div
            className={[
              "generation-timeline__item",
              isCurrent ? "is-current" : "",
              isDone ? "is-done" : "",
              isFailed ? "is-failed" : ""
            ].join(" ")}
            key={item.stage}
          >
            <Icon size={18} />
            <div>
              <strong>{isCurrent ? task.stage_label : item.label}</strong>
              <p>{isCurrent ? task.message : item.message}</p>
            </div>
          </div>
        );
      })}
    </div>
  );
}
