---
name: fund-report
description: Guide development and authoring for FundInsight Agent fund report generation. Use when Codex works on fund metrics JSON inputs, LLM-generated Markdown fund analysis reports, runtime prompts, chart specs, report planners, report guards, schema validation, tests, documentation, or safety boundaries for non-advisory fund intelligence reports.
---

# Fund Report

## When To Use This Skill

Use this Skill when working on FundInsight Agent features, documents, prompts, tests, or reviews related to generating Markdown fund analysis reports and chart specifications from structured fund metrics JSON.

This is a Codex App Skill. It is not an application runtime dependency. Do not implement business code that manually loads this Skill from `.agents/skills/fund-report/`.

## Purpose

Help Codex design and maintain a fund-report generation capability that:

- reads structured historical fund indicators
- prepares non-judgmental report context with a lightweight `report_planner`
- directly uses an LLM to generate a Markdown report
- emits chart specification JSON for later rendering
- grounds important conclusions in input metrics
- avoids rule-based analysis and fixed-weight scoring
- stays within non-advisory safety boundaries

## Required References

Read the relevant reference files before creating or changing report-related behavior:

- `references/indicator_glossary.md`: fund indicator definitions
- `references/report_structure.md`: required v0.2 report sections
- `references/analysis_principles.md`: interpretation rules and analysis chain
- `references/writing_style.md`: tone and formatting
- `references/safety_boundaries.md`: prohibited content and disclaimers

Use the sample assets when examples are needed:

- `assets/sample_input.json`
- `assets/sample_report.md`

## Runtime Boundary

The application runtime may use `prompts/fund_report_prompt.md` as the LLM template.

Do not:

- add `skill_loader.py`
- load `.agents/skills/fund-report/` from production code
- duplicate Skill reference files into runtime logic
- implement rule scoring as a substitute for LLM report generation

## Version 0.2 Product Flow

```text
Local fund metrics JSON
  -> schema validation
  -> report_planner prepares derived metrics, tables, chart drafts, and analysis focus
  -> prompts/fund_report_prompt.md rendering
  -> LLM call
  -> parse <report_markdown> and <chart_specs_json>
  -> report_guard checks obvious safety and structure violations
  -> Markdown report and chart_specs.json output
```

`report_planner` may organize data, calculate basic derived metrics, draft chart specs, and prepare LLM context. It must not judge whether a fund is good or bad, produce a rating, assign a score, or produce investment advice.

## Deep Analysis Requirement

Reports must not merely restate data. Important conclusions should follow this chain where possible:

```text
Data -> Comparison -> Interpretation -> Implication -> Caveat
```

- Data: cite the specific metric or field.
- Comparison: compare against benchmark, peer context, another period, or a related risk metric when available.
- Interpretation: explain what the relationship suggests about historical behavior.
- Implication: explain why the observation matters for research or monitoring.
- Caveat: state missing data, time-window limits, or uncertainty.

If comparison data is unavailable, say comparison is limited rather than fabricating context.

## Required v0.2 Report Content

The Markdown report should include:

- 核心结论
- 关键指标总览
- 收益分析
- 收益质量分析
- 风险控制分析
- 同类竞争力分析
- 基准比较分析
- 图表占位与图表解读
- 主要优势
- 主要风险
- 适合关注的场景
- 数据局限性
- 风险提示

The report should also include rich Markdown tables, at least five chart placeholders, and interpretations for every chart placeholder.

## Strict Prohibitions

Do not create behavior that:

- recommends buying, selling, holding, switching, redeeming, adding, or reducing positions
- recommends core allocation, portfolio allocation, bottom-position allocation, position sizing, or treating a fund as a portfolio core
- predicts future returns
- guarantees returns
- scores funds with fixed weights
- ranks funds as suitable or unsuitable for investment
- judges whether a fund is good or bad through `report_guard`
- fabricates missing data

## Grounding Requirement

All important report conclusions should cite input indicators where possible. If the input lacks the relevant metric, the report should say the conclusion is limited by missing data.
