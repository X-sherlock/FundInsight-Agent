import type { ChartSpec } from "../../features/reports/types";

interface MarkdownReportViewerProps {
  markdown: string;
  charts: ChartSpec[];
  hideTitle?: boolean;
}

export function MarkdownReportViewer({ markdown, charts, hideTitle = false }: MarkdownReportViewerProps) {
  const blocks = hideTitle ? dropFirstTitle(toBlocks(markdown)) : toBlocks(markdown);
  void charts;
  return (
    <article className="markdown-viewer">
      {blocks.map((block, index) => renderBlock(block, index))}
    </article>
  );
}

type MarkdownBlock =
  | { type: "heading"; level: number; text: string }
  | { type: "paragraph"; text: string }
  | { type: "list"; items: string[] }
  | { type: "table"; rows: string[][] };

function dropFirstTitle(blocks: MarkdownBlock[]): MarkdownBlock[] {
  const firstContentIndex = blocks.findIndex((block) => {
    if (block.type === "paragraph") {
      return block.text.trim();
    }
    return true;
  });
  if (firstContentIndex >= 0 && blocks[firstContentIndex].type === "heading" && blocks[firstContentIndex].level === 1) {
    return blocks.filter((_, index) => index !== firstContentIndex);
  }
  return blocks;
}

function toBlocks(markdown: string): MarkdownBlock[] {
  const lines = markdown.split(/\r?\n/);
  const blocks: MarkdownBlock[] = [];
  let index = 0;

  while (index < lines.length) {
    const line = lines[index].trim();
    if (!line) {
      index += 1;
      continue;
    }

    const chartMatch = /<!--\s*chart:\s*([a-zA-Z0-9_-]+)\s*-->/.exec(line);
    if (chartMatch) {
      index += 1;
      continue;
    }

    const headingMatch = /^(#{1,6})\s+(.+)$/.exec(line);
    if (headingMatch) {
      blocks.push({ type: "heading", level: headingMatch[1].length, text: headingMatch[2] });
      index += 1;
      continue;
    }

    if (line.startsWith("|")) {
      const rows: string[][] = [];
      while (index < lines.length && lines[index].trim().startsWith("|")) {
        const cells = lines[index]
          .trim()
          .replace(/^\|/, "")
          .replace(/\|$/, "")
          .split("|")
          .map((cell) => cell.trim());
        if (!cells.every((cell) => /^:?-{3,}:?$/.test(cell))) {
          rows.push(cells);
        }
        index += 1;
      }
      blocks.push({ type: "table", rows });
      continue;
    }

    if (/^[-*]\s+/.test(line) || /^\d+\.\s+/.test(line)) {
      const items: string[] = [];
      while (index < lines.length) {
        const itemMatch = /^(?:[-*]|\d+\.)\s+(.+)$/.exec(lines[index].trim());
        if (!itemMatch) {
          break;
        }
        items.push(itemMatch[1]);
        index += 1;
      }
      blocks.push({ type: "list", items });
      continue;
    }

    const paragraphLines: string[] = [];
    while (index < lines.length && lines[index].trim()) {
      if (/^(#{1,6})\s+/.test(lines[index].trim()) || lines[index].trim().startsWith("|")) {
        break;
      }
      paragraphLines.push(lines[index].trim());
      index += 1;
    }
    blocks.push({ type: "paragraph", text: paragraphLines.join(" ") });
  }

  return blocks;
}

function renderBlock(block: MarkdownBlock, index: number) {
  if (block.type === "heading") {
    const children = formatInline(block.text);
    if (block.level <= 1) {
      return <h2 key={index}>{children}</h2>;
    }
    if (block.level === 2) {
      return <h3 key={index}>{children}</h3>;
    }
    return <h4 key={index}>{children}</h4>;
  }
  if (block.type === "list") {
    return (
      <ul key={index}>
        {block.items.map((item) => (
          <li key={item}>{formatInline(item)}</li>
        ))}
      </ul>
    );
  }
  if (block.type === "table") {
    const [head, ...body] = block.rows;
    return (
      <div className="markdown-table-wrap" key={index}>
        <table>
          <thead>
            <tr>{head.map((cell) => <th key={cell}>{cell}</th>)}</tr>
          </thead>
          <tbody>
            {body.map((row, rowIndex) => (
              <tr key={`${row.join("-")}-${rowIndex}`}>
                {row.map((cell, cellIndex) => (
                  <td key={`${cell}-${cellIndex}`}>{formatInline(cell)}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  }
  return <p key={index}>{formatInline(block.text)}</p>;
}

function formatInline(text: string) {
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  return parts.map((part, index) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return <strong key={index}>{part.slice(2, -2)}</strong>;
    }
    return part;
  });
}
