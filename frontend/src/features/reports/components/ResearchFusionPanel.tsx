import type { ResearchContext, ResearchSignal, ResearchSourceType } from "../types";

const sourceTypeLabels: Record<ResearchSourceType, string> = {
  report: "研报",
  announcement: "公告",
  news: "新闻",
  internal_research: "内部投研材料"
};

const groups: Array<{ key: keyof ResearchContext; title: string }> = [
  { key: "positive_factors", title: "积极因素" },
  { key: "risk_notices", title: "风险提示" },
  { key: "key_events", title: "关键事件" },
  { key: "view_changes", title: "观点变化" }
];

export function ResearchFusionPanel({ context }: { context?: ResearchContext | null }) {
  const hasSignals = groups.some(({ key }) => ((context?.[key] as ResearchSignal[] | undefined) ?? []).length > 0);
  const materials = context?.source_materials ?? [];

  if (!context || (!hasSignals && materials.length === 0)) {
    return <div className="data-source-summary">暂无投研材料融合信息</div>;
  }

  return (
    <div className="research-fusion">
      {groups.map(({ key, title }) => {
        const signals = ((context[key] as ResearchSignal[] | undefined) ?? []).filter(Boolean);
        return (
          <section className="research-fusion__group" key={key}>
            <h3>{title}</h3>
            {signals.length > 0 ? (
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
                    {signal.evidence_text && <p>{signal.evidence_text}</p>}
                  </article>
                ))}
              </div>
            ) : (
              <div className="research-fusion__empty">暂无{title}</div>
            )}
          </section>
        );
      })}

      <section className="research-fusion__group">
        <h3>来源材料</h3>
        {materials.length > 0 ? (
          <div className="research-fusion__materials">
            {materials.map((material) => (
              <article className="research-fusion__material" key={material.material_id}>
                <strong>{material.title}</strong>
                <span>
                  {sourceTypeLabels[material.source_type]} / {material.source_name || "未填写来源"} /{" "}
                  {material.publish_date || "未填写日期"}
                </span>
              </article>
            ))}
          </div>
        ) : (
          <div className="research-fusion__empty">暂无来源材料</div>
        )}
      </section>
    </div>
  );
}
