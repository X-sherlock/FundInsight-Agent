"""Report orchestration for FundInsight Agent V0.1."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from fundinsight.data_loader import load_fund_metrics
from fundinsight.llm_client import LLMClient, OpenAILLMClient
from fundinsight.models import FundMetricsInput
from fundinsight.report_guard import GuardResult, check_report


DEFAULT_PROMPT_TEMPLATE_PATH = Path(__file__).resolve().parents[2] / "prompts" / "fund_report_prompt.md"


@dataclass(frozen=True)
class ReportResult:
    fund_metrics: FundMetricsInput
    prompt: str
    markdown: str
    guard_result: GuardResult


def load_prompt_template(path: str | Path = DEFAULT_PROMPT_TEMPLATE_PATH) -> str:
    template_path = Path(path)
    if not template_path.exists():
        raise FileNotFoundError(f"Prompt template does not exist: {template_path}")
    return template_path.read_text(encoding="utf-8")


def render_prompt(template: str, fund_metrics: FundMetricsInput) -> str:
    payload = json.dumps(fund_metrics.to_prompt_payload(), ensure_ascii=False, indent=2)
    if "{{fund_metrics_json}}" not in template:
        raise ValueError("Prompt template must contain {{fund_metrics_json}} placeholder.")
    return template.replace("{{fund_metrics_json}}", payload)


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
        template = load_prompt_template(self.prompt_template_path)
        prompt = render_prompt(template, fund_metrics)
        llm_client = self.llm_client or OpenAILLMClient()
        markdown = llm_client.generate(prompt)
        guard_result = check_report(markdown)
        return ReportResult(
            fund_metrics=fund_metrics,
            prompt=prompt,
            markdown=markdown,
            guard_result=guard_result,
        )
