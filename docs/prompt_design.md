# Prompt Design

## 1. Purpose

`prompts/fund_report_prompt.md` is the runtime prompt template used by the Python application when calling the LLM to generate a fund analysis report.

This file is separate from the Codex Skill under `.agents/skills/fund-report/`. The Skill guides Codex App; the prompt template guides application runtime LLM calls.

## 2. Design Goals

- Generate Markdown reports from structured fund metrics JSON.
- Ground important conclusions in specific input indicators.
- Preserve uncertainty when data is missing.
- Avoid investment advice and future-return prediction.
- Keep the output structure stable enough for `report_guard` checks.

## 3. Template Inputs

The prompt should receive:

- fund metrics JSON
- optional report language
- optional report date
- optional output section requirements

Version 1 can start with a single placeholder:

```text
{{fund_metrics_json}}
```

## 4. Prompt Boundaries

The prompt must instruct the model not to:

- recommend buying, selling, holding, switching, redeeming, adding, or reducing positions
- predict future returns
- guarantee returns
- calculate fixed-weight scores
- rank the fund as suitable or unsuitable for investment
- invent missing data

## 5. Grounding Requirement

For every important conclusion, the model should cite relevant input indicators where possible. Examples:

- "近 1 年收益率为 12.6%，同期基准为 9.1%，因此历史区间内存在 3.5% 的超额收益。"
- "近 1 年最大回撤为 -13.7%，说明观察期内存在一定净值回撤压力。"
- "由于缺少同类分位数据，无法判断其在同类基金中的相对位置。"

## 6. Guard Compatibility

The prompt should require stable section headings so `report_guard` can check structure without analyzing fund quality.
