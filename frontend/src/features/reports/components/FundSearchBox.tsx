import { Search } from "lucide-react";
import type { FundBrief } from "../types";

interface FundSearchBoxProps {
  query: string;
  funds: FundBrief[];
  selectedCode?: string;
  onQueryChange: (query: string) => void;
  onSelect: (fund: FundBrief) => void;
}

export function FundSearchBox({ query, funds, selectedCode, onQueryChange, onSelect }: FundSearchBoxProps) {
  return (
    <div className="fund-search">
      <label htmlFor="fund-query">基金代码或名称</label>
      <div className="fund-search__input">
        <Search size={18} />
        <input
          id="fund-query"
          value={query}
          onChange={(event) => onQueryChange(event.target.value)}
          placeholder="输入 000001 或基金名称"
        />
      </div>
      <div className="fund-search__results" aria-label="基金候选列表">
        {funds.map((fund) => (
          <button
            className={selectedCode === fund.code ? "fund-result is-selected" : "fund-result"}
            key={fund.code}
            type="button"
            onClick={() => onSelect(fund)}
          >
            <strong>{fund.name}</strong>
            <span>
              {fund.code} · {fund.type} · {fund.category}
            </span>
          </button>
        ))}
        {!funds.length && <div className="fund-search__empty">未找到匹配基金。</div>}
      </div>
    </div>
  );
}
