# fund-report

## When To Use This Skill

Use this Skill when working on FundInsight Agent features, documents, prompts, tests, or reviews related to generating Markdown fund analysis reports from structured fund metrics JSON.

This is a Codex App Skill. It is not an application runtime dependency. Do not implement business code that manually loads this Skill from `.agents/skills/fund-report/`.

## Purpose

Help Codex design and maintain a fund-report generation capability that:

- reads structured historical fund indicators
- directly uses an LLM to generate a Markdown report
- grounds important conclusions in input metrics
- avoids rule-based analysis and fixed-weight scoring
- stays within non-advisory safety boundaries

## Required References

Read the relevant reference files before creating or changing report-related behavior:

- `references/indicator_glossary.md`: fund indicator definitions
- `references/report_structure.md`: required report sections
- `references/analysis_principles.md`: interpretation rules
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

## First-Version Product Flow

```text
Local fund metrics JSON
  -> schema validation
  -> prompts/fund_report_prompt.md rendering
  -> LLM call
  -> Markdown report
  -> optional report_guard checks
```

## Strict Prohibitions

Do not create behavior that:

- recommends buying, selling, holding, switching, redeeming, adding, or reducing positions
- predicts future returns
- guarantees returns
- scores funds with fixed weights
- ranks funds as suitable or unsuitable for investment
- judges whether a fund is good or bad through `report_guard`
- fabricates missing data

## Grounding Requirement

All important report conclusions should cite input indicators where possible. If the input lacks the relevant metric, the report should say the conclusion is limited by missing data.

