import type { FundBrief } from "../features/reports/types";

export const mockFunds: FundBrief[] = [
  {
    code: "000001",
    name: "示例稳健成长混合基金",
    type: "混合型",
    company: "示例基金管理有限公司",
    benchmark: "沪深300指数",
    asOfDate: "2026-03-31",
    category: "主动混合型基金"
  },
  {
    code: "000002",
    name: "示例平衡研究基金",
    type: "偏股混合型",
    company: "示例基金管理有限公司",
    benchmark: "中证偏股基金指数",
    asOfDate: "2026-03-31",
    category: "偏股混合型基金"
  }
];
