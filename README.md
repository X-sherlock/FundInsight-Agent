# FundInsight Agent

FundInsight Agent is a Codex Skill and LLM based fund intelligence report system. v0.2 generates a customer-grade Markdown fund analysis report from structured fund metrics JSON and also emits `chart_specs.json` for later chart rendering.

The system is intended for research assistance, report drafting, and structured interpretation of historical fund indicators. It is not an investment advisory product.

## v0.2 Scope

- Input: one local JSON fund metrics file.
- Output: one Markdown report and one chart specification JSON file.
- Analysis engine: direct LLM generation using `prompts/fund_report_prompt.md`.
- Planner: `report_planner` prepares derived metrics, metric tables, chart drafts, missing fields, and analysis focus for the LLM.
- Parser: `report_parser` extracts `<report_markdown>` and `<chart_specs_json>` from the LLM output.
- Guardrail: `report_guard` checks required sections, prohibited expressions, chart placeholders, and minimum depth signals.

v0.2 deliberately does not include a rule analyzer, fixed-weight score, deterministic fund rating engine, Web UI, database, or investment recommendation workflow.

## Workflow

```text
Local JSON
  -> Pydantic schema validation
  -> report_planner context generation
  -> runtime prompt rendering
  -> LLM call
  -> report_parser extracts Markdown and chart specs
  -> report_guard checks safety and structure
  -> local Markdown and chart_specs.json output
```

## Project Structure

```text
FundInsightAgent/
  .agents/skills/fund-report/   Codex Skill guidance, not runtime code
  prompts/                      Runtime LLM prompt templates
  data/sample/                  Non-sensitive sample inputs
  data/outputs/                 Local generated outputs
  src/fundinsight/              Runtime package
  tests/                        Unit tests
```

## Installation

PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\activate
python -m pip install -e ".[dev]"
```

The RAG path uses the same project dependencies:

- `chromadb` for the persistent local vector index under `data/vector_store/chroma/`.
- `openai` for Bailian/DashScope-compatible embeddings and report-generation calls.
- `pypdf` for text extraction from searchable PDFs. OCR is intentionally not supported.

If these packages are missing in an existing virtual environment, reinstall the project:

```powershell
.venv\Scripts\python -m pip install -e ".[dev]"
```

## Environment Variables

### Bailian / DashScope

```powershell
$env:DASHSCOPE_API_KEY = "your_bailian_api_key"
```

The runtime uses Bailian's OpenAI-compatible endpoint with fixed model `deepseek-v4-flash`.

Default Bailian endpoint:

```text
https://dashscope.aliyuncs.com/compatible-mode/v1
```

You can override it with `DASHSCOPE_BASE_URL` or `BAILIAN_BASE_URL`.

### RAG Embeddings

By default, the project uses Bailian embeddings when `DASHSCOPE_API_KEY` or `ALIYUN_BAILIAN_API_KEY` is set. Without an API key it falls back to deterministic local hash embeddings so tests and offline development can still run, but production-like retrieval should use real embeddings.

```powershell
$env:FUNDINSIGHT_EMBEDDING_PROVIDER = "bailian"
$env:FUNDINSIGHT_EMBEDDING_MODEL = "text-embedding-v4"
```

For offline smoke tests:

```powershell
$env:FUNDINSIGHT_EMBEDDING_PROVIDER = "hash"
```

You can tune report-time retrieval count with:

```powershell
$env:FUNDINSIGHT_RAG_TOP_K = "12"
```

## CLI Usage

Generate a Markdown report and chart specs from the sample metrics file:

```powershell
fundinsight report --input data/sample/fund_metrics.json --output data/outputs/sample_report.md --chart-output data/outputs/sample_chart_specs.json
```

If `--chart-output` is omitted, the CLI writes chart specs next to the Markdown report using `<output stem>_chart_specs.json`.

### CLI RAG Usage

Import and index local research material first. Supported file types are `.txt`, `.md`, and text-based `.pdf`:

```powershell
fundinsight research import `
  --fund-code 000001 `
  --file data/funds/000001/research/materials/example_note.txt `
  --title "Example research note" `
  --source-type report `
  --source-name "Research Desk" `
  --publish-date 2026-05-01
```

Check indexing status:

```powershell
fundinsight research list --fund-code 000001
```

Generate a report with RAG retrieval enabled and save the exact fact card sent to the prompt:

```powershell
fundinsight report `
  --input data/funds/000001/metrics.json `
  --output data/outputs/000001_rag_report.md `
  --chart-output data/outputs/000001_rag_chart_specs.json `
  --include-research `
  --force-reextract `
  --fact-card-output data/outputs/000001_fact_card.json
```

When research materials exist, the API report task also auto-enables RAG unless the request sets `include_research` to `false`. Use `include_research: true` to force RAG on for a regenerated report, or `include_research: false` to force structured-metrics-only output.

## LLM Output Contract

The runtime prompt requires the LLM response to contain two tagged sections:

```text
<report_markdown>
完整 Markdown 报告
</report_markdown>

<chart_specs_json>
合法图表配置 JSON
</chart_specs_json>
```

The Markdown report must include core conclusions, key metric tables, return analysis, return quality analysis, risk control analysis, peer analysis, benchmark comparison, chart interpretation, strengths, risks, research scenarios, data limitations, and risk warnings.

The chart specs are written as:

```json
{
  "charts": [
    {
      "id": "returns_by_period",
      "title": "多周期收益表现",
      "type": "bar",
      "description": "展示基金在不同历史观察窗口内的收益表现。",
      "source_fields": ["metrics.performance.return_1y"],
      "series": [{"name": "基金收益", "values": [{"period": "1Y", "value": 0.126}]}],
      "encoding": {"x": "period", "y": "value"},
      "x_axis": "观察周期",
      "y_axis": "收益率",
      "value_unit": "decimal_percent",
      "notes": ["用于观察不同时间窗口的历史收益形态。"]
    }
  ]
}
```

Every Markdown chart placeholder must have a matching chart spec with the same `id`.

## API And Frontend Integration

Phase 4 adds a lightweight FastAPI backend for local frontend integration.

Start the backend:

```powershell
fundinsight-api
```

By default, API report tasks save reports even when `report_guard` finds structure or boundary issues. The report is returned with warning metadata so the frontend can display the guard issues without blocking local integration.

To make guard issues fail report tasks:

```powershell
fundinsight-api --enforce-report-guard
```

The same strict behavior can be enabled for `uvicorn fundinsight.api:app` with:

```powershell
$env:FUNDINSIGHT_ENFORCE_REPORT_GUARD = "true"
```

Or run directly:

```powershell
uvicorn fundinsight.api:app --reload
```

The API uses local metrics JSON files from `data/funds/{fund_code}/metrics.json`, with the sample fund available at `data/funds/000001/metrics.json`. Reports are stored under:

```text
reports/
  funds/{fund_code}/report.md
  funds/{fund_code}/chart_specs.json
  funds/{fund_code}/metadata.json
  funds/{fund_code}/source_metrics.json
  tasks/{task_id}.json
```

Main endpoints:

- `GET /api/funds?query=000001`
- `GET /api/funds/{fund_code}/metrics`
- `POST /api/reports/ensure`
- `GET /api/report-tasks/{task_id}`
- `GET /api/reports/{report_id}`

Start the frontend from `frontend/`:

```powershell
npm run dev
```

The frontend reads `VITE_API_BASE_URL` and defaults to `http://127.0.0.1:8000`. If the backend is unavailable in tests, the existing mock fallback remains available.

## Tests

```powershell
.venv\Scripts\python -m pytest
```

The tests cover schema validation, planner context generation, prompt rendering, tagged output parsing, report orchestration with a stub LLM client, guard checks, chart spec output, LLM client configuration, and CLI behavior.

## Safety Boundary

FundInsight Agent v0.2 must not output buy, sell, hold, timing, position-sizing, portfolio-allocation, core-allocation, or future-return prediction advice. It must not implement fixed-weight scoring, deterministic ratings, or suitability judgments.
