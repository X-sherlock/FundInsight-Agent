import { Save, Trash2 } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { Button } from "../../../components/ui/Button";
import {
  createResearchMaterial,
  deleteResearchMaterial,
  listResearchMaterials
} from "../../../services/reportApi";
import type { FundBrief, ResearchMaterial, ResearchSourceType } from "../types";

const sourceTypeOptions: Array<{ label: string; value: ResearchSourceType }> = [
  { label: "研报", value: "report" },
  { label: "公告", value: "announcement" },
  { label: "新闻", value: "news" },
  { label: "内部投研材料", value: "internal_research" }
];

const sourceTypeLabels: Record<ResearchSourceType, string> = {
  report: "研报",
  announcement: "公告",
  news: "新闻",
  internal_research: "内部投研材料"
};

interface ResearchMaterialsPanelProps {
  fund?: FundBrief;
  includeResearch: boolean;
  onIncludeResearchChange: (value: boolean) => void;
}

export function ResearchMaterialsPanel({
  fund,
  includeResearch,
  onIncludeResearchChange
}: ResearchMaterialsPanelProps) {
  const [materials, setMaterials] = useState<ResearchMaterial[]>([]);
  const [title, setTitle] = useState("");
  const [sourceType, setSourceType] = useState<ResearchSourceType>("report");
  const [sourceName, setSourceName] = useState("");
  const [publishDate, setPublishDate] = useState("");
  const [content, setContent] = useState("");
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fundCode = fund?.code;
  const hasMaterials = materials.length > 0;
  const materialCountText = useMemo(() => `${materials.length} 条已保存材料`, [materials.length]);

  useEffect(() => {
    let mounted = true;
    if (!fundCode) {
      setMaterials([]);
      return;
    }
    setLoading(true);
    setError(null);
    listResearchMaterials(fundCode)
      .then((items) => {
        if (mounted) {
          setMaterials(items);
        }
      })
      .catch((issue) => {
        if (mounted) {
          setError(issue instanceof Error ? issue.message : "投研材料列表加载失败。");
        }
      })
      .finally(() => {
        if (mounted) {
          setLoading(false);
        }
      });
    return () => {
      mounted = false;
    };
  }, [fundCode]);

  async function handleSave() {
    if (!fundCode) {
      return;
    }
    if (!title.trim()) {
      setError("标题不能为空。");
      return;
    }
    if (!content.trim()) {
      setError("正文内容不能为空。");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      await createResearchMaterial(fundCode, {
        title: title.trim(),
        content,
        source_type: sourceType,
        source_name: sourceName.trim() || null,
        publish_date: publishDate || null
      });
      setTitle("");
      setSourceName("");
      setPublishDate("");
      setContent("");
      setMaterials(await listResearchMaterials(fundCode));
    } catch (issue) {
      setError(issue instanceof Error ? issue.message : "投研材料保存失败。");
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(materialId: string) {
    if (!fundCode) {
      return;
    }
    setError(null);
    try {
      await deleteResearchMaterial(fundCode, materialId);
      setMaterials((current) => current.filter((item) => item.material_id !== materialId));
    } catch (issue) {
      setError(issue instanceof Error ? issue.message : "投研材料删除失败。");
    }
  }

  return (
    <div className="research-materials">
      <div className="research-materials__toggle">
        <label>
          <input
            type="checkbox"
            checked={includeResearch}
            onChange={(event) => onIncludeResearchChange(event.target.checked)}
          />
          融合投研材料生成增强报告
        </label>
        <span>{materialCountText}</span>
      </div>

      <div className="research-materials__form">
        <div>
          <label htmlFor="research-title">标题</label>
          <input
            id="research-title"
            value={title}
            disabled={!fund}
            onChange={(event) => setTitle(event.target.value)}
          />
        </div>
        <div>
          <label htmlFor="research-source-type">来源类型</label>
          <select
            id="research-source-type"
            value={sourceType}
            disabled={!fund}
            onChange={(event) => setSourceType(event.target.value as ResearchSourceType)}
          >
            {sourceTypeOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label htmlFor="research-source-name">来源名称</label>
          <input
            id="research-source-name"
            value={sourceName}
            disabled={!fund}
            onChange={(event) => setSourceName(event.target.value)}
          />
        </div>
        <div>
          <label htmlFor="research-publish-date">发布时间</label>
          <input
            id="research-publish-date"
            type="date"
            value={publishDate}
            disabled={!fund}
            onChange={(event) => setPublishDate(event.target.value)}
          />
        </div>
        <div className="research-materials__content">
          <label htmlFor="research-content">正文内容</label>
          <textarea
            id="research-content"
            value={content}
            disabled={!fund}
            rows={8}
            onChange={(event) => setContent(event.target.value)}
          />
        </div>
        <Button type="button" disabled={!fund || saving} onClick={handleSave}>
          <Save size={16} />
          保存材料
        </Button>
      </div>

      {error && <div className="form-error">{error}</div>}

      <div className="research-materials__list" aria-busy={loading}>
        {loading ? (
          <div className="data-source-summary">正在读取已保存材料...</div>
        ) : hasMaterials ? (
          materials.map((material) => (
            <article className="research-materials__item" key={material.material_id}>
              <div>
                <strong>{material.title}</strong>
                <span>
                  {sourceTypeLabels[material.source_type]} / {material.source_name || "未填写来源"} /{" "}
                  {material.publish_date || "未填写日期"}
                </span>
              </div>
              <Button type="button" variant="ghost" onClick={() => void handleDelete(material.material_id)}>
                <Trash2 size={16} />
                删除
              </Button>
            </article>
          ))
        ) : (
          <div className="data-source-summary">当前基金暂无已保存投研材料。</div>
        )}
      </div>
    </div>
  );
}
