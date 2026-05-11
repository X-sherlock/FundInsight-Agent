# Architecture

## 1. Architecture Goal

The architecture separates Codex Skill assets, runtime prompt templates, fund data handling, LLM invocation, report output, and safety checks. This keeps Version 1 small while leaving clear extension points for a future FastAPI backend and Web system.

## 2. Codex Skill vs Runtime Prompt

`.agents/skills/fund-report/` is a Codex App Skill. It helps Codex understand how to create, review, and evolve the fund-report capability.

The Python application must not implement a `skill_loader.py` or manually read `.agents/skills/fund-report/` at runtime.

Runtime report generation uses `prompts/fund_report_prompt.md` as the LLM prompt template.

## 3. Version 1 Runtime Flow

```text
CLI
  -> input loader
  -> schema validator
  -> runtime prompt renderer
  -> LLM provider
  -> Markdown writer
  -> optional report guard
```

## 4. Module Boundaries

### `interfaces`

Entry points for users or external systems.

Initial candidates:

- CLI command for generating one report from one local JSON file.
- Future FastAPI routers.

### `application`

Application use cases and orchestration.

Initial candidates:

- `GenerateFundReportUseCase`
- report-generation request and result models

### `domain`

Core domain models and validation concepts.

Initial candidates:

- fund metadata
- metric groups
- report metadata
- validation errors

The domain layer must not contain fixed-weight scoring or recommendation rules.

### `infrastructure`

External integrations and persistence adapters.

Initial candidates:

- local file input reader
- Markdown writer
- runtime prompt renderer
- LLM provider clients
- configuration loader

### `guards`

Report compliance checks.

Initial candidates:

- required section checker
- prohibited expression checker
- obvious boundary violation checker

The guard layer must not judge whether a fund is good or bad.

## 5. LLM Provider Boundary

LLM calls are hidden behind a provider interface, while the current runtime is intentionally fixed to Bailian `deepseek-v4-flash` as the default and only selectable report-generation model.

Conceptual interface:

```python
class LlmClient:
    def generate(self, prompt: str) -> str:
        ...
```

The implementation uses Bailian's OpenAI-compatible chat completions endpoint.

## 6. Guard Boundary

`report_guard` checks output compliance only:

- required headings exist
- non-advisory disclaimer exists
- prohibited recommendation wording is absent
- prohibited prediction wording is absent
- obvious boundary violations are flagged

It must not:

- score a fund
- classify a fund as good or bad
- create investment recommendations
- replace LLM analysis with deterministic rules

## 7. Future Backend Extension

FastAPI can be introduced by adding API routers under `interfaces/api` and calling the same application use cases used by the CLI. This avoids duplicating report-generation logic.
