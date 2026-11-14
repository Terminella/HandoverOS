"use client";

import { Bell, Leaf, LogOut, Search } from "lucide-react";
import type { CurrentUser, Project } from "../../lib/types";
import { useEffect, useState } from "react";
import { apiRequest } from "../../lib/api";
import { getStoredToken } from "../../lib/api";
import { clearToken } from "../../lib/auth";

const PROJECT_STORAGE_KEY = "handoveros-selected-project";

export default function Topbar({ projects, user }: { projects: Project[]; user: CurrentUser }) {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(null);

  useEffect(() => {
    const stored = typeof window !== "undefined"
      ? localStorage.getItem(PROJECT_STORAGE_KEY)
      : null;
    if (stored && projects.some((p) => p.id === stored)) {
      setSelectedProjectId(stored);
    } else if (projects.length > 0) {
      setSelectedProjectId(projects[0].id);
      localStorage.setItem(PROJECT_STORAGE_KEY, projects[0].id);
    }
  }, [projects]);

  function handleProjectChange(e: React.ChangeEvent<HTMLSelectElement>) {
    const id = e.target.value;
    setSelectedProjectId(id);
    localStorage.setItem(PROJECT_STORAGE_KEY, id);
  }

  function handleLogout() {
    clearToken();
    window.location.replace("/login");
  }

  return (
    <header className="topbar">
      <div className="topbar-brand">
        <Leaf size={24} aria-hidden="true" />
        <span>HandoverOS</span>
      </div>
      <label className="project-select">
        <span className="sr-only">Project</span>
        <select
          value={selectedProjectId ?? ""}
          onChange={handleProjectChange}
          aria-label="Project"
          disabled={projects.length === 0}
        >
          {projects.map((p) => (
            <option key={p.id} value={p.id}>
              {p.name}
            </option>
          ))}
        </select>
      </label>
      <div className="search" role="search">
        <Search size={18} aria-hidden="true" />
        <input
          type="search"
          placeholder="Search projects, sources, findings..."
          aria-label="Search"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />
      </div>
      <button type="button" className="icon-btn" aria-label="Notifications" disabled aria-disabled="true">
        <Bell size={20} aria-hidden="true" />
      </button>
      <button type="button" className="icon-btn" aria-label="Sign out" onClick={handleLogout}>
        <LogOut size={20} aria-hidden="true" />
      </button>
      <div className="avatar" title={user.name}>
        {user.initials}
      </div>
    </header>
  );
}
