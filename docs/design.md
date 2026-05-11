# FundInsight Agent Frontend Design

## Phase 3 Visual Direction

The Phase 3 frontend is a professional financial technology console rather than a single report page. The first screen is a Dashboard with clear entries for report creation, historical reports, fund metrics, comparison, batch analysis, and settings.

The design uses:

- Neutral light surfaces for information density and readability.
- Deep navy navigation to anchor the application shell.
- Low-saturation teal for primary actions and research status.
- Blue for mock/API state and amber/red only for risk or guard attention.
- Compact cards with 8px radius, restrained shadows, and table-first layouts where repeated information needs scanning.

## Page Structure

- `Dashboard`: system summary, module entry cards, runtime status, recent report list.
- `Report Create`: fund search, selected fund preview, minimal generation parameters, research boundary notice, mock generation progress.
- `Report Detail`: report header, core conclusions, key metrics, chart specs, Markdown report body, fund info, guard status, data quality details, risk notice.
- Reserved modules: historical reports, fund metrics, comparison, batch analysis, settings.

## Chart And Report Reading Rules

Charts are rendered from `chart_specs`; visual assets must not replace data charts. Chart cards always expose source fields so the report remains traceable to input metrics.

Markdown content is displayed in a constrained reading column with tables, lists, headings, and chart placeholders. The report detail page separates quick executive reading from the full body.

## Image Asset Policy

No generated image asset is required for the initial Phase 3 implementation. If later visual references or empty states are generated with image2 / gpt-image-2, use these paths and document each asset here:

- `docs/design/assets/dashboard-reference.png`: Dashboard visual reference.
- `docs/design/assets/report-detail-reference.png`: report detail layout reference.
- `docs/design/assets/report-generation-flow-image2.png`: image2-generated documentation flowchart for the backend report creation pipeline.
- `frontend/src/assets/empty-report-state.png`: business empty state for reports.
- `frontend/src/assets/report-cover-abstract.png`: subdued report header visual.

Generated images must support fund research, report reading, data quality, or workflow clarity. They should not be unrelated decoration, and chart images must not replace `chart_specs` rendering.
