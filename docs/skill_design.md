# Codex Skill Design

## 1. Skill Name

`fund-report`

## 2. Skill Location

`.agents/skills/fund-report`

## 3. Purpose

The Skill guides Codex App when designing, reviewing, and evolving fund report generation.

It contains the domain vocabulary, report outline, analysis principles, writing style, safety boundaries, and examples needed for consistent report generation.

The application runtime should not load this Skill manually. Runtime LLM calls use `prompts/fund_report_prompt.md`.

## 4. Required Files

- `SKILL.md`: main instructions and assembly order.
- `references/indicator_glossary.md`: definitions of fund indicators.
- `references/report_structure.md`: required report sections.
- `references/analysis_principles.md`: interpretation principles.
- `references/writing_style.md`: report tone and formatting guidance.
- `references/safety_boundaries.md`: prohibited content and required disclaimers.
- `assets/sample_input.json`: example structured input.
- `assets/sample_report.md`: example Markdown output.

## 5. Skill Responsibilities

The Skill should:

- Explain fund metrics in natural language.
- Compare indicators with benchmark and category context when provided.
- Surface uncertainty and missing data.
- Generate a coherent Markdown report.
- Avoid investment advice and future-return prediction.

The Skill should not:

- Assign fixed numeric scores.
- Use hard-coded indicator weights.
- Rank funds as buyable or unbuyable.
- Recommend buying, selling, holding, timing, or position sizing.

## 6. Runtime Prompt Relationship

The runtime prompt template is stored separately at `prompts/fund_report_prompt.md`.

When the prompt evolves, keep it aligned with the Skill's safety boundary, report structure, and grounding principles. Do not add runtime code that reads `.agents/skills/fund-report/`.

## 7. Versioning Direction

Future versions may add:

- Skill metadata and semantic versioning.
- More report templates.
- Dedicated comparison Skill.
- Skill test cases.
- Golden sample reports.
