# Roadmap

## Milestone 0: Project Skeleton

Status: current scope

- Create repository documentation.
- Define product requirements.
- Define architecture direction.
- Define the Codex Skill under `.agents/skills/fund-report/`.
- Define runtime prompt template under `prompts/`.
- Provide sample JSON input.
- Create Python package structure.

## Milestone 1: CLI Report Generation

- Implement JSON schema validation.
- Implement runtime prompt rendering from `prompts/fund_report_prompt.md`.
- Implement LLM provider abstraction.
- Implement report-generation orchestration.
- Implement Markdown file output.
- Implement `report_guard` for prohibited phrases, required sections, and obvious boundary violations.
- Add focused tests.

## Milestone 2: FastAPI Backend

- Add API endpoints for single-report generation.
- Add request and response models.
- Add report metadata handling.
- Add Bailian API key/base URL configuration and error handling.
- Add API-level tests.

## Milestone 3: Report Management

- Store generated reports and source inputs.
- Support report listing, retrieval, deletion, and regeneration.
- Add report status tracking.
- Add basic audit metadata.

## Milestone 4: Fund Comparison

- Support multiple fund inputs.
- Generate comparison reports with a dedicated runtime prompt and possibly a dedicated Codex Skill.
- Avoid deterministic fund ranking unless explicitly framed as non-advisory descriptive comparison.

## Milestone 5: Batch Analysis

- Support batch input files.
- Add asynchronous task execution.
- Add failure recovery and partial result reporting.

## Milestone 6: Report Q&A and Export

- Support Q&A over generated reports and source metrics.
- Add retrieval over report content.
- Keep answers within the same non-advisory safety boundaries.
- Support report export formats such as PDF or DOCX.

## Milestone 7: Prompt Version Management

- Track runtime prompt versions.
- Record which prompt version generated each report.
- Support prompt comparison and migration notes.
