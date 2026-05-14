import { useState } from "react";
import type {
  FactCard,
  FactCardSourceMaterial,
  ResearchAnalyzedMaterial,
  ResearchContext,
  ResearchMaterial,
  ResearchSignal,
  ResearchSourceType
} from "../types";

const sourceTypeLabels: Record<ResearchSourceType, string> = {
  report: "研报",
  announcement: "公告",
  news: "新闻",
  internal_research: "内部投研材料"
};

const sentimentLabels: Record<string, string> = {
  positive: "正面",
  neutral: "中性",
  negative: "负面",
  mixed: "多空交织",
  uncertain: "不确定",
  正面: "正面",
  中性: "中性",
  负面: "负面",
  多空交织: "多空交织",
  不确定: "不确定"
};

const groups: Array<{ key: keyof ResearchContext; title: string }> = [
  { key: "positive_factors", title: "积极因素" },
  { key: "risk_notices", title: "风险提示" },
  { key: "key_events", title: "关键事件" },
  { key: "view_changes", title: "观点变化" }
];
const INITIAL_RETRIEVED_CHUNK_LIMIT = 3;

export function ResearchFusionPanel({
  context,
  factCard
}: {
  context?: ResearchContext | null;
  factCard?: FactCard | null;
}) {
  if (factCard?.retrieved_chunks?.length) {
    return <FactCardPanel factCard={factCard} />;
  }
  return <LegacyResearchContextPanel context={context} />;
}

function FactCardPanel({ factCard }: { factCard: FactCard }) {
  const [showAll, setShowAll] = useState(false);
  const retrievedChunks = [...factCard.retrieved_chunks]
    .filter(isUsableRetrievedChunk)
    .filter(hasChunkAnalysis)
    .sort((left, right) => right.relevance_score - left.relevance_score);
  const visibleChunks = showAll ? retrievedChunks : retrievedChunks.slice(0, INITIAL_RETRIEVED_CHUNK_LIMIT);
  const hiddenCount = Math.max(0, retrievedChunks.length - visibleChunks.length);

  return (
    <div className="research-fusion">
      <section className="research-fusion__group">
        <div className="research-fusion__signals">
          {visibleChunks.map((chunk) => (
            <article className="research-fusion__signal" key={chunk.chunk_id}>
              <strong>{chunk.title}</strong>
              <div className="research-fusion__meta">
                <span>相关度：{chunk.relevance_score.toFixed(2)}</span>
                <span>
                  来源类型：{sourceTypeLabels[chunk.source_type]}（{chunk.source_type}）
                </span>
                {chunk.publish_date && <span>发布时间：{chunk.publish_date}</span>}
                <span>chunk_id：{chunk.chunk_id}</span>
              </div>
              {hasChunkAnalysis(chunk) && <ChunkAnalysis chunk={chunk} />}
              <div className="research-fusion__source-detail">{formatDetailedSource(chunk)}</div>
              <EvidenceDisclosure text={chunk.evidence_text} />
            </article>
          ))}
        </div>
        {retrievedChunks.length > INITIAL_RETRIEVED_CHUNK_LIMIT && (
          <button className="research-fusion__more" type="button" onClick={() => setShowAll((value) => !value)}>
            {showAll ? "收起" : `展示更多（${hiddenCount}）`}
          </button>
        )}
      </section>

      {factCard.source_materials.length > 0 && (
        <section className="research-fusion__group">
          <h3>相关材料链接</h3>
          <MaterialList materials={factCard.source_materials} />
        </section>
      )}
    </div>
  );
}

function ChunkAnalysis({ chunk }: { chunk: FactCard["retrieved_chunks"][number] }) {
  const sentiment = normalizeSentiment(chunk.sentiment_label);
  const hasExcerpt = Boolean(chunk.evidence_excerpt?.trim());
  return (
    <div className="research-fusion__analysis">
      {(chunk.analysis_title || sentiment) && (
        <div className="research-fusion__analysis-header">
          {chunk.analysis_title && (
            <div>
              <span>AI 解读</span>
              <strong>{chunk.analysis_title}</strong>
            </div>
          )}
          {sentiment && (
            <span className={`research-fusion__sentiment research-fusion__sentiment--${sentiment.className}`}>
              {sentiment.label}
            </span>
          )}
        </div>
      )}
      {chunk.material_summary && (
        <div className="research-fusion__analysis-block">
          <span>材料摘要</span>
          <p>{chunk.material_summary}</p>
        </div>
      )}
      {hasExcerpt && (
        <div className="research-fusion__analysis-block">
          <span>证据原文摘录</span>
          <p>{chunk.evidence_excerpt}</p>
        </div>
      )}
    </div>
  );
}

function LegacyResearchContextPanel({ context }: { context?: ResearchContext | null }) {
  const hasSignals = groups.some(({ key }) => ((context?.[key] as ResearchSignal[] | undefined) ?? []).length > 0);
  const analyzedMaterials = ((context?.analyzed_materials ?? []) as ResearchAnalyzedMaterial[]).filter(
    hasContributingSignals
  );
  const sourceMaterials = context?.source_materials ?? [];
  const materials = analyzedMaterials.length > 0 ? analyzedMaterials : sourceMaterials;
  const materialsTitle = analyzedMaterials.length > 0 ? "本次纳入分析材料" : "本次引用材料";

  if (!context || !hasSignals) {
    return null;
  }

  return (
    <div className="research-fusion">
      {groups.map(({ key, title }) => {
        const signals = ((context[key] as ResearchSignal[] | undefined) ?? []).filter(Boolean);
        if (signals.length === 0) {
          return null;
        }
        return (
          <section className="research-fusion__group" key={key}>
            <h3>{title}</h3>
            <div className="research-fusion__signals">
              {signals.map((signal, index) => (
                <article className="research-fusion__signal" key={signal.signal_id ?? `${key}-${index}`}>
                  <strong>{signal.summary || "未命名信号"}</strong>
                  <div className="research-fusion__meta">
                    {signal.importance && <span>重要性：{signal.importance}</span>}
                    {typeof signal.confidence === "number" && <span>置信度：{signal.confidence.toFixed(2)}</span>}
                    {signal.source_type && <span>来源类型：{sourceTypeLabels[signal.source_type]}</span>}
                    {signal.publish_date && <span>发布时间：{signal.publish_date}</span>}
                  </div>
                  {signal.evidence_text && <EvidenceDisclosure text={signal.evidence_text} />}
                </article>
              ))}
            </div>
          </section>
        );
      })}

      {materials.length > 0 && (
        <section className="research-fusion__group">
          <h3>{materialsTitle}</h3>
          <MaterialList materials={materials} />
        </section>
      )}
    </div>
  );
}

function MaterialList({
  materials
}: {
  materials: Array<ResearchAnalyzedMaterial | ResearchMaterial | FactCardSourceMaterial>;
}) {
  return (
    <div className="research-fusion__materials">
      {materials.map((material) => (
        <article className="research-fusion__material" key={material.material_id}>
          {material.source_url ? (
            <a href={material.source_url} target="_blank" rel="noreferrer" title={material.title}>
              {material.title}
            </a>
          ) : (
            <strong title={material.title}>{material.title}</strong>
          )}
          <span>
            {sourceTypeLabels[material.source_type]} / {material.source_name || "未填写来源"} /{" "}
            {material.publish_date || "未填写日期"}
          </span>
          {isAnalyzedMaterial(material) && (
            <span>
              信号数：{material.signal_count ?? 0}
              {typeof material.chunk_count === "number" ? ` / 分片数：${material.chunk_count}` : ""}
            </span>
          )}
          {materialFileLabel(material) && <span title={materialFileTitle(material)}>{materialFileLabel(material)}</span>}
        </article>
      ))}
    </div>
  );
}

function EvidenceDisclosure({ text }: { text: string }) {
  return (
    <details className="research-fusion__evidence">
      <summary>证据原文</summary>
      <p>{text}</p>
    </details>
  );
}

function isAnalyzedMaterial(
  material: ResearchAnalyzedMaterial | ResearchMaterial | FactCardSourceMaterial
): material is ResearchAnalyzedMaterial {
  return "signal_count" in material || "chunk_count" in material;
}

function hasContributingSignals(material: ResearchAnalyzedMaterial): boolean {
  return typeof material.signal_count === "number" && material.signal_count > 0;
}

function isUsableRetrievedChunk(chunk: FactCard["retrieved_chunks"][number]): boolean {
  if (chunk.relevance_score < 0.01) {
    return false;
  }
  return !looksLikeWebShell(chunk.evidence_text);
}

function hasChunkAnalysis(chunk: FactCard["retrieved_chunks"][number]): boolean {
  return Boolean(
    chunk.analysis_title?.trim() &&
      chunk.material_summary?.trim() &&
      chunk.sentiment_label?.trim() &&
      chunk.evidence_excerpt?.trim()
  );
}

function normalizeSentiment(value?: string | null): { label: string; className: string } | null {
  const raw = value?.trim();
  if (!raw) {
    return null;
  }
  const label = sentimentLabels[raw] ?? raw;
  const className =
    label === "正面"
      ? "positive"
      : label === "负面"
        ? "negative"
        : label === "多空交织"
          ? "mixed"
          : label === "不确定"
            ? "uncertain"
            : "neutral";
  return { label, className };
}

function formatDetailedSource(chunk: FactCard["retrieved_chunks"][number]): string {
  const parts = [
    `标题《${chunk.title}》`,
    `来源类型：${chunk.source_type}`,
    chunk.publish_date ? `发布时间：${chunk.publish_date}` : null,
    chunk.source_url ? `URL：${chunk.source_url}` : null,
    chunk.original_file_path ? `本地文件路径：${chunk.original_file_path}` : null,
    `chunk_id：${chunk.chunk_id}`
  ].filter(Boolean);
  return `详细来源：${parts.join("，")}`;
}

function looksLikeWebShell(text: string): boolean {
  const markers = [
    "登录",
    "手机号",
    "获取验证码",
    "忘记密码",
    "立即注册",
    "扫码登录",
    "下载APP",
    "客服电话",
    "收藏本站",
    "安全登录",
    "安全退出",
    "网站导航",
    "热点推荐",
    "帮助中心",
    "鐧诲綍",
    "鎵嬫満",
    "楠岃瘉",
    "蹇樿瀵嗙爜",
    "绔嬪嵆娉ㄥ唽",
    "涓嬭浇APP",
    "瀹夊叏鐧诲綍"
  ];
  const markerCount = markers.filter((marker) => text.includes(marker)).length;
  if (markerCount < 4) {
    return false;
  }
  const lines = text
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean);
  const firstSection = lines.slice(0, 40).join("\n");
  const firstSectionMarkerCount = markers.filter((marker) => firstSection.includes(marker)).length;
  const shortLineRatio = lines.filter((line) => line.length <= 12).length / Math.max(lines.length, 1);
  const denseMenuWords = firstSection.match(/登录|基金|股票|板块|课程|首页|搜索|财富|鐧诲綍|鍩洪噾|鑲＄エ/g)?.length ?? 0;
  return firstSectionMarkerCount >= 3 || (shortLineRatio > 0.55 && denseMenuWords >= 8);
}

function materialFileLabel(material: ResearchAnalyzedMaterial | ResearchMaterial | FactCardSourceMaterial): string | null {
  if ("file_name" in material && material.file_name) {
    return material.file_name;
  }
  if ("original_file_path" in material && material.original_file_path) {
    return material.original_file_path.split(/[\\/]/).pop() || material.original_file_path;
  }
  return null;
}

function materialFileTitle(material: ResearchAnalyzedMaterial | ResearchMaterial | FactCardSourceMaterial): string | undefined {
  if ("original_file_path" in material && material.original_file_path) {
    return material.original_file_path;
  }
  if ("file_name" in material && material.file_name) {
    return material.file_name;
  }
  return undefined;
}
