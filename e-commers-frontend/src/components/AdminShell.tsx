import type { ReactNode } from "react";
import { NavLink } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

type AdminShellProps = {
  children: ReactNode;
  title: string;
  subtitle: string;
};

const navClass = ({ isActive }: { isActive: boolean }) =>
  `admin-nav-link${isActive ? " is-active" : ""}`;

export default function AdminShell({ children, title, subtitle }: AdminShellProps) {
  const { user } = useAuth();

  return (
    <div className="admin-shell">
      <aside className="admin-sidebar">
        <div className="admin-sidebar-brand">
          <div className="admin-sidebar-logo">
            <span className="material-symbols-outlined">smart_toy</span>
          </div>
          <div>
            <h1>NeuralCore</h1>
            <p>Enterprise Admin</p>
          </div>
        </div>

        <nav className="admin-nav">
          <NavLink className={navClass} end to="/admin/ai">
            <span className="material-symbols-outlined">dashboard</span>
            Dashboard
          </NavLink>
          <NavLink className={navClass} to="/admin/ai/recommendations">
            <span className="material-symbols-outlined">auto_awesome</span>
            Recommendations
          </NavLink>
          <NavLink className={navClass} to="/admin/ai/training">
            <span className="material-symbols-outlined">neurology</span>
            Training Jobs
          </NavLink>
          <NavLink className={navClass} to="/admin/ai/moderation">
            <span className="material-symbols-outlined">rule_settings</span>
            Moderation
          </NavLink>
        </nav>

        <div className="admin-usage-card">
          <div className="admin-usage-label">Usage Limit</div>
          <div className="admin-usage-bar">
            <span style={{ width: "72%" }} />
          </div>
          <p>72% of monthly compute tokens</p>
        </div>
      </aside>

      <div className="admin-content-wrap">
        <header className="admin-topbar">
          <div>
            <h2>{title}</h2>
            <p>{subtitle}</p>
          </div>

          <div className="admin-topbar-actions">
            <div className="admin-search">
              <span className="material-symbols-outlined">search</span>
              <input defaultValue="" placeholder="Search models, jobs, or logs..." />
            </div>
            <button className="icon-ghost-button" type="button">
              <span className="material-symbols-outlined">notifications</span>
            </button>
            <div className="admin-user-chip">
              <div className="admin-user-avatar">{(user?.full_name ?? "Admin").charAt(0).toUpperCase()}</div>
              <div>
                <strong>{user?.full_name ?? "Admin User"}</strong>
                <span>{user?.role === "admin" ? "Super Admin" : "AI Console"}</span>
              </div>
            </div>
          </div>
        </header>

        <main className="admin-main">{children}</main>
      </div>
    </div>
  );
}
