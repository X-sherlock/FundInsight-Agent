# FundInsight Agent Repository Guide

## Project Purpose

FundInsight Agent is a Codex Skill and LLM based fund intelligence evaluation system. Version 1 reads a structured fund metrics JSON file and directly calls a large language model to generate a Markdown fund analysis report.

This repository must not implement a rule analyzer, fixed-weight scoring formula, deterministic fund rating engine, or investment recommendation workflow.

## Codex Skill Boundary

- The Codex Skill lives under `.agents/skills/fund-report/`.
- The Skill is a Codex App capability used to guide development and authoring.
- Business runtime code must not implement `skill_loader.py` or manually read the Codex Skill as an application dependency.
- Runtime LLM calls may use `prompts/fund_report_prompt.md` as the report-generation template.

## Core Constraints

- Version 1 must directly invoke an LLM to generate reports.
- Reports must be based on the input indicators as much as possible.
- Important conclusions should cite specific input metrics or explicitly state when data is missing.
- The system is not an investment advisory product.
- Do not output buy, sell, hold, timing, position-sizing, or future-return predictions.
- `report_guard` may check prohibited wording, required sections, and obvious boundary violations only.
- `report_guard` must not judge whether a fund is good or bad.

## Expected Version 1 Flow

1. Load a local JSON file containing structured fund metrics.
2. Validate the input shape.
3. Render `prompts/fund_report_prompt.md` with the JSON payload.
4. Call an LLM provider.
5. Write a Markdown report.
6. Run optional guard checks for prohibited expressions, required sections, and obvious boundary violations.

## Directory Principles

- `.agents/skills/fund-report/` contains the Codex Skill.
- `prompts/` contains runtime prompt templates used by the Python application.
- `src/fundinsight_agent/` contains application code.
- `docs/` contains product, architecture, data, and prompt design documents.
- `data/sample/` contains non-sensitive sample inputs only.
- `reports/` may be used for local generated Markdown reports and should not contain private user data.

## Frontend Design Guidelines

- FundInsight Agent frontend experiences should feel professional, clear, modern, and appropriate for a financial technology system.
- Pages should not be rough demos; they should aim for the product completeness expected from a real system.
- Report generation is only one system capability. Frontend structure must leave room for future modules such as fund metrics display, fund comparison, batch analysis, and historical report management.
- When needed, `image2` / `gpt-image-2` may be used to generate page visual references, illustrations, empty states, report header images, or design assets.
- Image generation outputs must support system functionality and visual consistency, and must not introduce unrelated decoration.
- All image assets should be placed under `frontend/src/assets` or `docs/design/assets`, with their purpose documented in `docs/design.md`.

## Coding Guidance

- Prefer small modules with explicit responsibilities.
- Keep LLM provider integrations behind interfaces.
- Keep runtime prompts in `prompts/`, not scattered across business code.
- Do not add Skill-loading code for `.agents/skills`.
- Avoid introducing a database, Web framework, queue, or UI until required by a later milestone.
- Use tests for schema validation, guard checks, prompt rendering, and report orchestration once implementation begins.
