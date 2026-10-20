import { useEffect, useState } from "react";
import { Bot, ClipboardList, Shield } from "lucide-react";
import { AdminWorkspace } from "@/components/AdminWorkspace";
import { AssistantPanel } from "@/components/AssistantPanel";
import { TaskWorkspace } from "@/components/TaskWorkspace";
import { useRole } from "@/context/RoleContext";

type WorkspaceView = "tasks" | "assistant" | "admin";

export default function App() {
  const { currentUserId, currentRole, currentUser, users, switchUser, refreshUsers } = useRole();
  const [view, setView] = useState<WorkspaceView>("tasks");
  const activeRole = currentUser?.role ?? currentRole;
  const isAdmin = activeRole === "admin";

  useEffect(() => {
    if (!isAdmin && view === "admin") setView("tasks");
  }, [isAdmin, view]);

  return (
    <main className="taskflow-shell">
      <nav className="topbar" aria-label="Workspace">
        <a className="brand" href="/" aria-label="TaskFlow home"><span className="brand-glyph">T</span>taskflow</a>
        <div className="workspace-switcher">
          <span>WORKSPACE IDENTITY</span>
          <select
            aria-label="Select user or administrator workspace"
            value={currentUserId}
            onChange={(event) => {
              const selected = users.find((user) => user.id === Number(event.target.value));
              if (selected) switchUser(selected);
            }}
          >
            {users.map((user) => <option key={user.id} value={user.id}>{user.name} · {user.role}</option>)}
          </select>
        </div>
      </nav>
      <div className="workspace-layout">
        <aside className="workspace-rail">
          <div className="rail-caption">CURRENT SPACE</div>
          <div className={`role-stamp ${activeRole}`}>
            <span className="role-dot" />
            <div><strong>{isAdmin ? "Administrator" : "Personal workspace"}</strong><small>{currentUser?.email ?? "Loading identity…"}</small></div>
          </div>
          <div className="rail-rule" />
          <p className="rail-note">{isAdmin
            ? "This assistant can review system-wide tasks and perform administrator actions."
            : "This assistant can only see and manage tasks owned by your account."}</p>
          <nav className="workspace-nav" aria-label="Main navigation">
            <button type="button" className={view === "tasks" ? "active" : ""} onClick={() => setView("tasks")}><ClipboardList size={16} />Tasks</button>
            <button type="button" className={view === "assistant" ? "active" : ""} onClick={() => setView("assistant")}><Bot size={16} />Assistant</button>
            {isAdmin && <button type="button" className={view === "admin" ? "active" : ""} onClick={() => setView("admin")}><Shield size={16} />Admin</button>}
          </nav>
          <div className="rail-bottom">TASKFLOW<br />ASSISTED WORKSPACE</div>
        </aside>
        <div className="chat-stage">
          {view === "tasks" && <TaskWorkspace key={`tasks-${activeRole}-${currentUserId}`} isAdmin={isAdmin} currentUserId={currentUserId} users={users} />}
          {view === "assistant" && <AssistantPanel key={`${activeRole}-${currentUserId}`} role={activeRole} name={currentUser?.name ?? "there"} />}
          {view === "admin" && isAdmin && <AdminWorkspace key={`admin-${currentUserId}`} currentUserId={currentUserId} users={users} onUsersChanged={refreshUsers} />}
        </div>
      </div>
    </main>
  );
}