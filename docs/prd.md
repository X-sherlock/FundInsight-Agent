# Product Requirements Document

## 1. Product Name

FundInsight Agent

## 2. Product Positioning

FundInsight Agent is a Codex Skill and LLM based fund intelligence evaluation system. The first version generates structured Markdown fund analysis reports from fund indicator JSON by directly calling a large language model.

The product is intended for research assistance, report drafting, and structured interpretation of fund metrics. It is not an investment advisory tool.

## 3. Target Users

- Individual researchers who want a readable fund metric summary.
- Analysts who need a draft report based on standardized fund indicators.
- Developers building a fund analysis backend or report-management platform.

## 4. Version 1 Goals

- Accept a local JSON file as input.
- Validate that the file contains required fund metadata and indicators.
- Render `prompts/fund_report_prompt.md` as the runtime LLM template.
- Directly call a configured LLM provider.
- Output a Markdown report.
- Optionally run a guard check for report structure, prohibited expressions, and obvious boundary violations.
- Keep Codex Skill assets under `.agents/skills/fund-report/`.

## 5. Version 1 Non-Goals

- Do not implement rule-based analysis.
- Do not implement a fixed-weight fund score.
- Do not rank funds.
- Do not manually load Codex Skill files in business runtime code.
- Do not output buy, sell, hold, timing, or allocation advice.
- Do not predict future returns.
- Do not implement a full backend, database, Web UI, or report Q&A system.

## 6. Functional Requirements

### FR-1 Local JSON Input

The system reads a local JSON file containing fund metadata, performance metrics, risk metrics, drawdown metrics, fee metrics, manager information, and benchmark information where available.

### FR-2 Runtime Prompt Rendering

The application uses `prompts/fund_report_prompt.md` as the LLM report-generation template. The runtime prompt must instruct the model to ground important conclusions in input indicators.

### FR-3 Codex Skill

The Codex Skill under `.agents/skills/fund-report/` provides authoring and development guidance for Codex App. It is not loaded by application runtime code.

### FR-4 LLM Report Generation

The system must call a configured LLM provider to generate the report. The LLM response is treated as the primary analysis output.

### FR-5 Markdown Output

The generated report must be saved as a Markdown file.

### FR-6 Guard Check

The optional guard module may check:

- Required report sections.
- Prohibited recommendation expressions.
- Prohibited return-prediction expressions.
- Obvious boundary violations.

The guard module must not assign quality labels, compute scores, or determine whether the fund is good or bad.

## 7. Safety Requirements

- Reports must include a clear non-advisory statement.
- Reports must avoid direct investment recommendations.
- Reports must not imply guaranteed returns.
- Reports must not claim future performance can be predicted from historical metrics.
- Important conclusions should cite the input metrics used as evidence, or state that evidence is missing.

## 8. Success Criteria

- A sample JSON file can be used to generate a Markdown report through an LLM.
- The generated report follows the required structure.
- Guard checks can flag prohibited expressions without performing investment judgment.
- The module structure can support later FastAPI and Web extensions.
