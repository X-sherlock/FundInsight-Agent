import { Clock3 } from "lucide-react";
import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Card } from "../components/ui/Card";
import { GenerationFailurePanel } from "../features/reports/components/GenerationFailurePanel";
import { ReportGenerationTimeline } from "../features/reports/components/ReportGenerationTimeline";
import type { ReportTaskStatus } from "../features/reports/types";
import { ensureReport, getReportTask } from "../services/reportApi";

export function ReportTaskPage() {
  const { taskId } = useParams();
  const navigate = useNavigate();
  const [task, setTask] = useState<ReportTaskStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [retrying, setRetrying] = useState(false);

  useEffect(() => {
    if (!taskId) {
      setError("缺少报告任务 ID。");
      return;
    }
    const resolvedTaskId = taskId;
    let mounted = true;
    let redirectTimer: number | undefined;

    async function loadTask() {
      try {
        const data = await getReportTask(resolvedTaskId);
        if (!mounted) {
          return;
        }
        setTask(data);
        if (data.status === "completed" && data.report_id) {
          redirectTimer = window.setTimeout(() => {
            navigate(`/reports/${data.report_id}`);
          }, 650);
        }
      } catch (issue) {
        if (mounted) {
          setError(issue instanceof Error ? issue.message : "报告任务加载失败。");
        }
      }
    }

    void loadTask();
    const interval = window.setInterval(loadTask, 1800);
    return () => {
      mounted = false;
      window.clearInterval(interval);
      if (redirectTimer) {
        window.clearTimeout(redirectTimer);
      }
    };
  }, [navigate, taskId]);

  async function handleRetry() {
    if (!task) {
      return;
    }
    setRetrying(true);
    setError(null);
    try {
      const response = await ensureReport({ fund_code: task.fund_code });
      if (response.task_id) {
        navigate(`/reports/tasks/${response.task_id}`);
      } else if (response.report_id) {
        navigate(`/reports/${response.report_id}`);
      }
    } catch (issue) {
      setError(issue instanceof Error ? issue.message : "重新生成请求失败。");
    } finally {
      setRetrying(false);
    }
  }

  if (error) {
    return <div className="page-error">{error}</div>;
  }

  if (!task) {
    return <div className="page-loading">正在读取报告生成状态...</div>;
  }

  return (
    <div className="page-stack">
      <section className="report-task-hero">
        <div>
          <p className="eyebrow">Report Generation</p>
          <h1>{task.stage_label}</h1>
          <p>{task.message}</p>
        </div>
        <span>
          <Clock3 size={16} />
          {formatTime(task.updated_at)}
        </span>
      </section>

      {task.status === "failed" ? (
        <GenerationFailurePanel task={task} retrying={retrying} onRetry={handleRetry} />
      ) : (
        <Card title="生成阶段" eyebrow="Task Status">
          <ReportGenerationTimeline task={task} />
        </Card>
      )}
    </div>
  );
}

function formatTime(value: string): string {
  if (!value) {
    return "等待状态更新";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return `最近更新 ${date.toLocaleTimeString()}`;
}
