import { Outlet } from "react-router-dom";
import { SidebarNav } from "./SidebarNav";
import { TopBar } from "./TopBar";

export function AppShell() {
  return (
    <div className="app-shell">
      <SidebarNav />
      <main className="app-main">
        <TopBar />
        <div className="page-wrap">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
