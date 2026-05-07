export function GenerationProgress({ active }: { active: boolean }) {
  if (!active) {
    return null;
  }
  return (
    <div className="generation-progress" role="status">
      <span />
      <div>
        <strong>正在生成 mock 报告</strong>
        <p>前端正在按未来 API 契约模拟创建流程。</p>
      </div>
    </div>
  );
}
