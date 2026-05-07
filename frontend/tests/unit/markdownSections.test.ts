import { describe, expect, it } from "vitest";
import { extractChartPlaceholders, extractMarkdownSections, extractMarkdownTitle } from "../../src/lib/markdownSections";

describe("markdownSections", () => {
  it("extracts headings and chart placeholders", () => {
    const markdown = `# Title

## 核心结论
content

<!-- chart: returns_by_period -->
`;

    expect(extractMarkdownSections(markdown)).toEqual([
      { level: 1, title: "Title", content: "" },
      { level: 2, title: "核心结论", content: "content\n\n<!-- chart: returns_by_period -->" }
    ]);
    expect(extractChartPlaceholders(markdown)).toEqual(["returns_by_period"]);
    expect(extractMarkdownTitle(markdown)).toBe("Title");
  });
});
