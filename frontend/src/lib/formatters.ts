export function formatPercent(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "缺失";
  }
  return `${(value * 100).toFixed(2)}%`;
}

export function formatChartValue(value: number | null | undefined, unit?: string): string {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "缺失";
  }
  if (unit === "decimal_percent") {
    return formatPercent(value);
  }
  if (unit === "mixed" && Math.abs(value) <= 1) {
    return formatPercent(value);
  }
  if (unit === "number") {
    return value.toFixed(2);
  }
  return String(value);
}

export function formatDateTime(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return new Intl.DateTimeFormat("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit"
  }).format(date);
}
