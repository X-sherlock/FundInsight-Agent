import { Files, GitCompare, Layers3 } from "lucide-react";
import { FeatureEntryCard } from "./FeatureEntryCard";

export function FutureModuleGrid() {
  return (
    <div className="feature-grid">
      <FeatureEntryCard
        title="基金指标展示"
        description="预留指标卡、趋势图和数据质量解释空间。"
        to="/funds"
        icon={Files}
      />
      <FeatureEntryCard
        title="基金对比"
        description="预留多基金横向研究和差异解释空间。"
        to="/compare"
        icon={GitCompare}
      />
      <FeatureEntryCard
        title="批量分析"
        description="预留批量任务、失败复核和进度追踪空间。"
        to="/batch"
        icon={Layers3}
      />
    </div>
  );
}
