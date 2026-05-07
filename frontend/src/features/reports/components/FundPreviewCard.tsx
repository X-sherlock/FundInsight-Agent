import type { FundBrief } from "../types";

export function FundPreviewCard({ fund }: { fund?: FundBrief }) {
  if (!fund) {
    return (
      <div className="fund-preview fund-preview--empty">
        <strong>等待选择基金</strong>
        <span>选择基金后将展示后端指标数据日期、业绩基准和基金类型信息。</span>
      </div>
    );
  }

  return (
    <div className="fund-preview">
      <div>
        <p className="eyebrow">Selected Fund</p>
        <h2>{fund.name}</h2>
      </div>
      <dl>
        <div>
          <dt>基金代码</dt>
          <dd>{fund.code}</dd>
        </div>
        <div>
          <dt>基金类型</dt>
          <dd>{fund.type}</dd>
        </div>
        <div>
          <dt>业绩基准</dt>
          <dd>{fund.benchmark}</dd>
        </div>
        <div>
          <dt>数据日期</dt>
          <dd>{fund.asOfDate}</dd>
        </div>
      </dl>
    </div>
  );
}
