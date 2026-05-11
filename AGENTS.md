# FundInsight Agent Repository Guide

## Project Purpose

FundInsight Agent is a Codex Skill guided and LLM based fund intelligence report system. Version 1 reads a structured fund metrics JSON file and directly calls a large language model to generate a Markdown fund analysis report.

This repository must not implement a rule analyzer, fixed-weight scoring formula, deterministic fund rating engine, investment recommendation workflow, target-price workflow, or future-return prediction workflow.

## Codex Skill Boundary

- The Codex Skill lives under `.agents/skills/fund-report/`.
- The Skill is a Codex App capability used to guide development and authoring.
- Business runtime code must not implement `skill_loader.py` or manually read the Codex Skill as an application dependency.
- Runtime LLM calls may use `prompts/fund_report_prompt.md` as the report-generation template.
- Runtime report generation must use runtime prompts under `prompts/`; `.agents/skills/fund-report/` is not a runtime dependency.

## Core Constraints

- Version 1 must directly invoke an LLM to generate reports.
- Reports must be based on the input indicators as much as possible.
- Important conclusions should cite specific input metrics or explicitly state when data is missing.
- The system is not an investment advisory product.
- Do not output investment advice, buy recommendations, sell recommendations, hold recommendations, add-position recommendations, reduce-position recommendations, target prices, timing advice, position-sizing guidance, portfolio-allocation guidance, or future-return predictions.
- `report_guard` may check prohibited wording, required sections, and obvious boundary violations only.
- `report_guard` must not judge whether a fund is good or bad.

## Runtime Architecture

- The actual backend runtime package is `src/fundinsight`.
- New runtime features should be added under `src/fundinsight` unless there is a clear and documented reason to do otherwise.
- `src/fundinsight_agent` is currently a placeholder package for layered architecture ideas. Do not refactor or move runtime code into it without an explicit project decision.
- Current report output uses file-based storage, not a database.
- Report files are stored under `reports/funds/{fund_code}/` with Markdown, chart specs, source metrics, and metadata files.

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
- `src/fundinsight/` contains the actual backend runtime code.
- `src/fundinsight_agent/` is a placeholder package and should not be the default target for new features.
- `docs/` contains product, architecture, data, and prompt design documents.
- `data/sample/` contains non-sensitive sample inputs only.
- `reports/` may be used for local generated Markdown reports and should not contain private user data.

## Unstructured Research Material Rules

The first phase of unstructured research material fusion may ingest fund research reports, announcements, news, and investment research notes to extract positive factors, risk notices, key events, and view changes. It does not add Q&A.

- Unstructured research material may only explain, supplement, contextualize, or add risk warnings to the structured metric analysis.
- Unstructured research material must not override conclusions grounded in structured indicators. If material conflicts with structured metrics, the report should state the discrepancy and preserve the metric-based limitation.
- Phase 1 must not introduce a database, vector database, Q&A API, complex PDF/DOCX parsing, or OCR.
- Phase 1 should use file-based storage for unstructured material with these paths:
  - `data/funds/{fund_code}/research/materials/`
  - `data/funds/{fund_code}/research/extracted_signals.json`
  - `data/funds/{fund_code}/research/fusion_context.json`
- LLM extraction results must pass Pydantic schema validation before they can be used by report generation.
- Each extracted unstructured signal must preserve `source_type`, `doc_id`, `material_id`, `evidence_text`, and `confidence`.
- `evidence_text` must come from the original material. Do not fabricate or paraphrase it as evidence text.
- When no unstructured material exists for a fund, report generation must continue to follow the original structured-metrics-only logic.

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
- Avoid introducing a database, vector database, Web framework, queue, Q&A interface, complex document parser, OCR pipeline, or UI until required by a later milestone.
- Do not add new production dependencies unless the necessity is explained and the dependency is appropriate for the current milestone.
- Use tests for schema validation, guard checks, prompt rendering, and report orchestration once implementation begins.
- After code changes, run `.venv\Scripts\python -m pytest`. If a change introduces behavior without existing coverage, add the smallest relevant unit test.
