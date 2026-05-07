export function CoreConclusionPanel({ conclusions }: { conclusions: string[] }) {
  return (
    <div className="conclusion-panel">
      {conclusions.map((item, index) => (
        <div className="conclusion-panel__item" key={item}>
          <span>{index + 1}</span>
          <p>{item}</p>
        </div>
      ))}
    </div>
  );
}
