import { LoaderCircle, Trash2, UploadCloud } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { Button } from "../../../components/ui/Button";
import {
  deleteResearchMaterial,
  listResearchMaterials,
  uploadResearchMaterial
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
  const [sourceUrl, setSourceUrl] = useState("");
  const [publishDate, setPublishDate] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fundCode = fund?.code;
  const hasMaterials = materials.length > 0;
  const materialCountText = useMemo(() => `${materials.length} 条已入库材料`, [materials.length]);
  const uploadStatusText = file
    ? `正在处理 ${file.name}，系统会完成上传、分片和向量入库，请稍等片刻。`
    : "正在上传并处理材料，请稍等片刻。";

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
          setError(issue instanceof Error ? issue.message : "材料列表加载失败。");
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

  async function handleUpload() {
    if (!fundCode || !file) {
      return;
    }
    const resolvedTitle = title.trim() || file.name;
    setSaving(true);
    setError(null);
    try {
      await uploadResearchMaterial(fundCode, {
        file,
        title: resolvedTitle,
        source_type: sourceType,
        source_name: sourceName.trim() || null,
        source_url: sourceUrl.trim() || null,
        publish_date: publishDate || null
      });
      setTitle("");
      setSourceName("");
      setSourceUrl("");
      setPublishDate("");
      setFile(null);
      setMaterials(await listResearchMaterials(fundCode));
    } catch (issue) {
      setError(issue instanceof Error ? issue.message : "材料上传或向量入库失败。");
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
      setError(issue instanceof Error ? issue.message : "材料删除失败。");
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
          使用 RAG 相关材料增强报告
        </label>
        <span>{materialCountText}</span>
      </div>

      <div className="research-materials__form">
        <div>
          <label htmlFor="research-file">材料文件</label>
          <input
            id="research-file"
            type="file"
            accept=".pdf,.txt,.md,text/plain,text/markdown,application/pdf"
            disabled={!fund || saving}
            onChange={(event) => setFile(event.target.files?.[0] ?? null)}
          />
        </div>
        <div>
          <label htmlFor="research-title">标题</label>
          <input
            id="research-title"
            value={title}
            placeholder={file?.name ?? "未填写时使用文件名"}
            disabled={!fund || saving}
            onChange={(event) => setTitle(event.target.value)}
          />
        </div>
        <div>
          <label htmlFor="research-source-type">来源类型</label>
          <select
            id="research-source-type"
            value={sourceType}
            disabled={!fund || saving}
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
            disabled={!fund || saving}
            onChange={(event) => setSourceName(event.target.value)}
          />
        </div>
        <div>
          <label htmlFor="research-source-url">来源链接</label>
          <input
            id="research-source-url"
            value={sourceUrl}
            disabled={!fund || saving}
            onChange={(event) => setSourceUrl(event.target.value)}
          />
        </div>
        <div>
          <label htmlFor="research-publish-date">发布时间</label>
          <input
            id="research-publish-date"
            type="date"
            value={publishDate}
            disabled={!fund || saving}
            onChange={(event) => setPublishDate(event.target.value)}
          />
        </div>
        <Button type="button" disabled={!fund || !file || saving} onClick={() => void handleUpload()}>
          {saving ? (
            <LoaderCircle className="research-materials__upload-spinner" size={16} aria-hidden="true" />
          ) : (
            <UploadCloud size={16} />
          )}
          {saving ? "正在入库..." : "上传并入库"}
        </Button>
      </div>

      {saving && (
        <div className="research-materials__upload-status" role="status" aria-live="polite">
          <LoaderCircle className="research-materials__upload-spinner" size={18} aria-hidden="true" />
          <div>
            <strong>正在上传并解析材料</strong>
            <span>{uploadStatusText}</span>
          </div>
        </div>
      )}

      {error && <div className="form-error">{error}</div>}

      <div className="research-materials__list" aria-busy={loading || saving}>
        {loading ? (
          <div className="data-source-summary">正在读取已入库材料...</div>
        ) : hasMaterials ? (
          materials.map((material) => (
            <article className="research-materials__item" key={material.material_id}>
              <div>
                {material.source_url ? (
                  <a href={material.source_url} target="_blank" rel="noreferrer">
                    <strong>{material.title}</strong>
                  </a>
                ) : (
                  <strong>{material.title}</strong>
                )}
                <span>
                  {sourceTypeLabels[material.source_type]} / {material.source_name || "未填写来源"} /{" "}
                  {material.publish_date || "未填写日期"}
                </span>
                <span>
                  {material.file_name || "文本材料"} / 分片 {material.chunk_count ?? 0} /{" "}
                  {material.vector_status === "indexed" ? "已向量化" : material.vector_status || "待入库"}
                </span>
              </div>
              <Button type="button" variant="ghost" onClick={() => void handleDelete(material.material_id)}>
                <Trash2 size={16} />
                删除
              </Button>
            </article>
          ))
        ) : (
          <div className="data-source-summary">当前基金暂无已入库材料。</div>
        )}
      </div>
    </div>
  );
}
