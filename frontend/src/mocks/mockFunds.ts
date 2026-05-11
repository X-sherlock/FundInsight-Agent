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
  },
  {
    code: "000003",
    name: "示例低波红利股票基金",
    type: "股票型",
    company: "示例基金管理有限公司",
    benchmark: "中证红利指数",
    asOfDate: "2026-03-31",
    category: "主动股票型基金"
  },
  {
    code: "000004",
    name: "示例固收增强债券基金",
    type: "债券型",
    company: "示例基金管理有限公司",
    benchmark: "中债综合财富指数",
    asOfDate: "2026-03-31",
    category: "混合债券型二级基金"
  },
  {
    code: "000005",
    name: "示例科技创新股票基金",
    type: "股票型",
    company: "示例基金管理有限公司",
    benchmark: "中证TMT产业主题指数",
    asOfDate: "2026-03-31",
    category: "科技主题股票型基金"
  }
];
