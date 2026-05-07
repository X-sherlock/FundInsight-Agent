export interface MarkdownSection {
  level: number;
  title: string;
  content: string;
}

export function extractMarkdownSections(markdown: string): MarkdownSection[] {
  const lines = markdown.split(/\r?\n/);
  const sections: MarkdownSection[] = [];
  let current: MarkdownSection | null = null;

  for (const line of lines) {
    const match = /^(#{1,6})\s+(.+)$/.exec(line);
    if (match) {
      if (current) {
        sections.push({ ...current, content: current.content.trim() });
      }
      current = {
        level: match[1].length,
        title: match[2].trim(),
        content: ""
      };
      continue;
    }
    if (current) {
      current.content += `${line}\n`;
    }
  }

  if (current) {
    sections.push({ ...current, content: current.content.trim() });
  }
  return sections;
}

export function extractChartPlaceholders(markdown: string): string[] {
  return Array.from(markdown.matchAll(/<!--\s*chart:\s*([a-zA-Z0-9_-]+)\s*-->/g)).map(
    (match) => match[1]
  );
}

export function extractMarkdownTitle(markdown: string): string {
  const titleMatch = markdown.match(/^#\s+(.+)$/m);
  return titleMatch?.[1]?.trim() || "分析报告";
}
