"""Report orchestration for FundInsight Agent v0.2."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from fundinsight.data_loader import load_fund_metrics
from fundinsight.llm_client import LLMClient, OpenAILLMClient
from fundinsight.models import ChartSpec, FundMetricsInput, ReportPlan
from fundinsight.report_guard import GuardResult, check_chart_specs, check_report
from fundinsight.report_parser import parse_report_output
from fundinsight.report_planner import build_report_plan


DEFAULT_PROMPT_TEMPLATE_PATH = Path(__file__).resolve().parents[2] / "prompts" / "fund_report_prompt.md"


@dataclass(frozen=True)
class ReportResult:
    fund_metrics: FundMetricsInput
    report_plan: ReportPlan
    prompt: str
    markdown: str
    chart_specs: list[ChartSpec]
    guard_result: GuardResult


def load_prompt_template(path: str | Path = DEFAULT_PROMPT_TEMPLATE_PATH) -> str:
    template_path = Path(path)
    if not template_path.exists():
        raise FileNotFoundError(f"Prompt template does not exist: {template_path}")
    return template_path.read_text(encoding="utf-8")


def render_prompt(template: str, report_plan: ReportPlan) -> str:
    payload = json.dumps(report_plan.to_prompt_payload(), ensure_ascii=False, indent=2)
    placeholder = "{{report_context_json}}"
    if placeholder not in template:
        raise ValueError("Prompt template must contain {{report_context_json}} placeholder.")
    return template.replace(placeholder, payload)


class ReportAgent:
    def __init__(
        self,
        llm_client: LLMClient | None = None,
        prompt_template_path: str | Path = DEFAULT_PROMPT_TEMPLATE_PATH,
    ) -> None:
        self.llm_client = llm_client
        self.prompt_template_path = Path(prompt_template_path)

    def generate_report(self, input_path: str | Path) -> ReportResult:
        fund_metrics = load_fund_metrics(input_path)
        report_plan = build_report_plan(fund_metrics)
        template = load_prompt_template(self.prompt_template_path)
        prompt = render_prompt(template, report_plan)
        llm_client = self.llm_client or OpenAILLMClient()
        raw_output = llm_client.generate(prompt)
        parsed_output = parse_report_output(raw_output)
        guard_result = _combine_guard_results(
            check_report(parsed_output.report_markdown),
            check_chart_specs(parsed_output.report_markdown, parsed_output.chart_specs),
        )
        return ReportResult(
            fund_metrics=fund_metrics,
            report_plan=report_plan,
            prompt=prompt,
            markdown=parsed_output.report_markdown,
            chart_specs=parsed_output.chart_specs,
            guard_result=guard_result,
        )


def _combine_guard_results(*results: GuardResult) -> GuardResult:
    issues = tuple(issue for result in results for issue in result.issues)
    return GuardResult(issues)
