# FundInsight Agent

FundInsight Agent is a Codex Skill and LLM based fund intelligence evaluation system. Version 1 focuses on one capability: read structured fund metrics from a local JSON file and call a large language model to generate a Markdown fund analysis report.

The project is designed to evolve into a broader system for fund metric display, report management, fund comparison, batch analysis, report Q&A, report export, and Prompt version management.

## Version 1 Scope

- Input: local JSON fund metrics file.
- Output: Markdown fund analysis report.
- Analysis engine: direct LLM generation.
- Codex Skill: `.agents/skills/fund-report/` for Codex App guidance.
- Runtime prompt: `prompts/fund_report_prompt.md` for application LLM calls.
- Guardrail: optional `report_guard` for prohibited expressions, required sections, and obvious boundary violations.

Version 1 deliberately does not include rule-based scoring, fixed-weight fund ranking, portfolio advice, or future-return prediction.

## Non-Goals

- No buy, sell, hold, timing, or allocation recommendations.
- No prediction of future returns.
- No deterministic score based on fixed indicator weights.
- No manual runtime loader for Codex Skill files.
- No complete Web UI, FastAPI backend, database, or batch pipeline in the first milestone.

## Planned Structure

```text
FundInsightAgent/
  .agents/
    skills/
      fund-report/
        references/
        assets/
  prompts/
  docs/
  data/
    sample/
  src/
    fundinsight/
      cli.py
      data_loader.py
      llm_client.py
      models.py
      report_agent.py
      report_guard.py
    fundinsight_agent/
      application/
      domain/
      infrastructure/
      interfaces/
      guards/
  tests/
```

## First-Version Workflow

```text
Local JSON -> Schema validation -> Runtime prompt rendering -> LLM call -> Markdown report -> Guard check
```

## Codex Skill

The first Codex Skill lives in `.agents/skills/fund-report`. It defines indicator meanings, report structure, analysis principles, writing style, safety boundaries, and examples for Codex-assisted work.

## Development Status

V0.1 adds a local CLI flow:

```text
Local JSON -> Pydantic schema validation -> Runtime prompt rendering -> OpenAI LLM call -> Markdown report -> Guard check -> Local output file
```

The runtime code uses `prompts/fund_report_prompt.md` as the report-generation template. The Codex Skill under `.agents/skills/fund-report/` is development guidance only and is not loaded by the application.

## Installation

PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\activate
python -m pip install -e ".[dev]"
```

## Environment Variables

PowerShell:

```powershell
$env:OPENAI_API_KEY = "your_api_key"
$env:OPENAI_MODEL = "gpt-4o-mini"
```

cmd:

```bat
set OPENAI_API_KEY=your_api_key
set OPENAI_MODEL=gpt-4o-mini
```

`OPENAI_API_KEY` is required. `OPENAI_MODEL` is optional and defaults to `gpt-4o-mini`.

## CLI Usage

Generate a Markdown report from the sample metrics file:

```bash
fundinsight report --input data/sample/fund_metrics.json --output data/outputs/000001_report.md
```

The CLI validates the input JSON, renders `prompts/fund_report_prompt.md`, calls OpenAI, checks the generated Markdown with `report_guard`, and writes the report only when guard checks pass.

## Tests

```bash
pytest
```

The tests cover schema validation, sample data loading, prompt rendering, report orchestration with a fake LLM client, guard checks, and CLI output behavior.

## Safety Boundary

FundInsight Agent V0.1 does not implement a rule analyzer, fixed-weight score, fund rating formula, or investment recommendation workflow. Generated reports must not contain buy, sell, hold, timing, position-sizing, or future-return prediction advice.
