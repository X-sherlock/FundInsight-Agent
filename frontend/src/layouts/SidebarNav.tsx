import { BarChart3, FileClock, FilePlus2, Gauge, GitCompare, Home, Layers3, Settings } from "lucide-react";
import { NavLink } from "react-router-dom";

const navItems = [
  { to: "/dashboard", label: "Dashboard", icon: Home },
  { to: "/reports/new", label: "生成分析报告", icon: FilePlus2 },
  { to: "/reports/history", label: "历史报告", icon: FileClock },
  { to: "/funds", label: "基金指标", icon: Gauge },
  { to: "/compare", label: "基金对比", icon: GitCompare },
  { to: "/batch", label: "批量分析", icon: Layers3 },
  { to: "/settings", label: "系统设置", icon: Settings }
];

export function SidebarNav() {
  return (
    <aside className="sidebar">
      <div className="sidebar__brand">
        <div className="sidebar__logo">
          <BarChart3 size={21} />
        </div>
        <div>
          <strong>FundInsight</strong>
          <span>Agent Console</span>
        </div>
      </div>
      <nav className="sidebar__nav" aria-label="主导航">
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              className={({ isActive }) => (isActive ? "sidebar__link is-active" : "sidebar__link")}
              to={item.to}
              key={item.to}
            >
              <Icon size={18} />
              <span>{item.label}</span>
            </NavLink>
          );
        })}
      </nav>
    </aside>
  );
}
