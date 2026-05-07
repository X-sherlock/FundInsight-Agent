import { ShieldCheck } from "lucide-react";

export function TopBar() {
  return (
    <header className="topbar">
      <div>
        <p className="eyebrow">Mock Mode</p>
        <h1>基金智能研究工作台</h1>
      </div>
      <div className="topbar__status">
        <ShieldCheck size={16} />
        <span>Non-advisory research boundary</span>
      </div>
    </header>
  );
}
