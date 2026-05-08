import type { ReactNode } from "react";

export function CoreConclusionPanel({ conclusions }: { conclusions: string[] }) {
  return (
    <div className="conclusion-panel">
      {conclusions.map((item, index) => (
        <div className="conclusion-panel__item" key={`${index}-${item}`}>
          <span>{index + 1}</span>
          <p>{renderInlineMarkdown(item)}</p>
        </div>
      ))}
    </div>
  );
}

function renderInlineMarkdown(text: string): ReactNode[] {
  const normalizedText = text.replace(/^\*(?!\*)/, "**");
  const nodes: ReactNode[] = [];
  const pattern = /\*\*(.+?)\*\*/g;
  let lastIndex = 0;
  let match: RegExpExecArray | null;

  while ((match = pattern.exec(normalizedText)) !== null) {
    if (match.index > lastIndex) {
      nodes.push(normalizedText.slice(lastIndex, match.index));
    }
    nodes.push(<strong key={`${match.index}-${match[1]}`}>{match[1]}</strong>);
    lastIndex = match.index + match[0].length;
  }

  if (lastIndex < normalizedText.length) {
    nodes.push(normalizedText.slice(lastIndex));
  }

  return nodes.length ? nodes : [normalizedText];
}
