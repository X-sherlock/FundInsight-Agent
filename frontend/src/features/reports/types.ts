export type ReportStatus = "generating" | "passed" | "warning" | "failed";

export interface FundBrief {
  code: string;
  name: string;
  type: string;
  company: string;
  benchmark: string;
  asOfDate: string;
  category: string;
}

export interface FundBriefApi {
  code: string;
  name: string;
  type: string;
  company: string;
  benchmark: string;
  as_of_date: string;
  category: string;
}

export interface GuardIssue {
  code: string;
  message: string;
}

export interface GuardResult {
  passed: boolean;
  issues: GuardIssue[];
}

export interface ChartSeries {
  name: string;
  values: Array<Record<string, string | number | null>>;
}

export interface ChartEncoding {
  x?: string;
  y?: string;
  category?: string;
  value?: string;
}

export interface ChartSpec {
  id: string;
  title: string;
  type: "bar" | "pie" | "line" | string;
  description: string;
  source_fields: string[];
  series: ChartSeries[];
  encoding: ChartEncoding;
  x_axis?: string;
  y_axis?: string;
  value_unit?: string;
  notes: string[];
}

export interface ChartSpecsPayload {
  charts: ChartSpec[];
}

export interface KeyMetric {
  label: string;
  value: string;
  tone?: "neutral" | "positive" | "warning";
  helper: string;
}

export interface DataQuality {
  missing_fields: string[];
  notes: string[];
}

export interface ReportRecord {
  report_id: string;
  status: ReportStatus;
  fund: FundBrief;
  as_of_date: string;
  created_at: string;
  core_conclusions: string[];
  key_metrics: KeyMetric[];
  markdown: string;
  chart_specs: ChartSpecsPayload;
  research_context?: ResearchContext | null;
  fact_card?: FactCard | null;
  guard_result: GuardResult;
  data_quality: DataQuality;
}

export interface CreateReportRequest {
  fund_code: string;
  input_mode: "sample" | "manual";
  metrics_input_id: string;
}

export interface CreateReportResponse {
  report_id: string;
  status: "generating";
}

export interface EnsureReportRequest {
  fund_code: string;
  force_regenerate?: boolean;
  include_research?: boolean | null;
  research_material_ids?: string[] | null;
  force_reextract?: boolean;
}

export interface EnsureReportResponse {
  mode: "existing" | "created" | "running";
  status: string;
  report_id?: string | null;
  report_url?: string | null;
  task_id?: string | null;
  status_url?: string | null;
}

export type ReportTaskStage =
  | "queued"
  | "loading_data"
  | "planning_context"
  | "extracting_research"
  | "fusing_research"
  | "llm_generating"
  | "parsing_charts"
  | "quality_checking"
  | "saving_report"
  | "completed"
  | "failed";

export interface ReportTaskStatus {
  task_id: string;
  fund_code: string;
  status: ReportTaskStage;
  stage: ReportTaskStage;
  stage_label: string;
  message: string;
  report_id?: string | null;
  error?: GuardIssue | null;
  include_research?: boolean | null;
  research_material_ids?: string[] | null;
  force_reextract?: boolean;
  created_at: string;
  updated_at: string;
}

export type ResearchSourceType = "report" | "announcement" | "news" | "internal_research";

export interface ResearchMaterial {
  material_id: string;
  fund_code: string;
  title: string;
  source_type: ResearchSourceType;
  source_name?: string | null;
  source_url?: string | null;
  publish_date?: string | null;
  file_name?: string | null;
  original_file_path?: string | null;
  extracted_text_path?: string | null;
  chunk_count?: number | null;
  vector_status?: "pending" | "indexed" | "failed";
  vector_error?: string | null;
  created_at: string;
}

export interface ResearchAnalyzedMaterial {
  material_id: string;
  title: string;
  source_type: ResearchSourceType;
  source_name?: string | null;
  source_url?: string | null;
  publish_date?: string | null;
  chunk_count?: number | null;
  signal_count?: number | null;
}

export interface ResearchMaterialCreateRequest {
  title: string;
  content: string;
  source_type: ResearchSourceType;
  source_name?: string | null;
  source_url?: string | null;
  publish_date?: string | null;
}

export interface ResearchSignal {
  signal_id?: string;
  fund_code?: string;
  material_id?: string;
  chunk_id?: string | null;
  signal_type?: string;
  summary?: string;
  detail?: string | null;
  category?: string | null;
  signal_date?: string | null;
  impact_direction?: string | null;
  importance?: string | null;
  confidence?: number | null;
  evidence_text?: string;
  source_type?: ResearchSourceType;
  publish_date?: string | null;
}

export interface ResearchContext {
  fund_code?: string;
  positive_factors?: ResearchSignal[];
  risk_notices?: ResearchSignal[];
  key_events?: ResearchSignal[];
  view_changes?: ResearchSignal[];
  source_materials?: ResearchMaterial[];
  analyzed_materials?: ResearchAnalyzedMaterial[];
  limitations?: string[];
  generated_at?: string;
}

export interface RetrievedResearchChunk {
  chunk_id: string;
  material_id: string;
  fund_code: string;
  chunk_index: number;
  evidence_text: string;
  relevance_score: number;
  source_type: ResearchSourceType;
  title: string;
  source_name?: string | null;
  source_url?: string | null;
  publish_date?: string | null;
  file_name?: string | null;
  original_file_path?: string | null;
  analysis_title?: string | null;
  material_summary?: string | null;
  sentiment_label?: string | null;
  evidence_excerpt?: string | null;
}

export interface FactCardSourceMaterial {
  material_id: string;
  title: string;
  source_type: ResearchSourceType;
  source_name?: string | null;
  source_url?: string | null;
  publish_date?: string | null;
  file_name?: string | null;
  original_file_path?: string | null;
  chunk_count?: number | null;
}

export interface FactCard {
  fund_code: string;
  source_metrics: Record<string, unknown>;
  derived_metrics: Record<string, unknown>;
  metric_tables: Record<string, unknown>;
  missing_fields: string[];
  data_notes: string[];
  retrieved_chunks: RetrievedResearchChunk[];
  source_materials: FactCardSourceMaterial[];
  limitations: string[];
  generated_at?: string;
}

export interface FundMetricsResponse {
  fund: FundBrief;
  metrics: Record<string, unknown>;
  raw: Record<string, unknown>;
}

export interface DashboardSummary {
  total_reports: number;
  passed_reports: number;
  warning_reports: number;
  mock_mode: boolean;
  latest_report?: ReportRecord;
  recent_reports: ReportRecord[];
  system_status: Array<{
    label: string;
    value: string;
    status: "ok" | "warning" | "mock";
  }>;
}
