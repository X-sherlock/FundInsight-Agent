import type { DataQuality } from "../types";

export function SourceFieldsDrawer({ dataQuality }: { dataQuality: DataQuality }) {
  return (
    <details className="source-drawer">
      <summary>查看数据局限</summary>
      <div className="source-drawer__content">
        <div>
          <h3>数据完整性</h3>
          <p>当前报告存在 {dataQuality.missing_fields.length} 项数据缺口，具体影响已在报告正文的数据局限性中说明。</p>
        </div>
        {dataQuality.notes.length > 0 && (
          <div>
            <h3>数据说明</h3>
            <ul>
              {dataQuality.notes.map((note) => (
                <li key={note}>{note}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </details>
  );
}
