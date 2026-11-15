"use client";

import { Bell, Leaf, LogOut, Search } from "lucide-react";
import type { CurrentUser, Project } from "../../lib/types";
import { useEffect, useMemo, useState } from "react";
import { clearToken } from "../../lib/auth";
import {
  PROJECT_CHANGE_EVENT,
  PROJECT_STORAGE_KEY,
  deduplicateProjects,
  isKnownProject,
  publishProjectSelection,
} from "../../lib/project-selection";

export default function Topbar({ projects, user }: { projects: Project[]; user: CurrentUser }) {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(null);
  const uniqueProjects = useMemo(() => deduplicateProjects(projects), [projects]);

  useEffect(() => {
    const stored = typeof window !== "undefined"
      ? localStorage.getItem(PROJECT_STORAGE_KEY)
      : null;
    if (isKnownProject(uniqueProjects, stored)) {
      setSelectedProjectId(stored);
    } else if (uniqueProjects.length > 0) {
      setSelectedProjectId(uniqueProjects[0].id);
      localStorage.setItem(PROJECT_STORAGE_KEY, uniqueProjects[0].id);
    }
  }, [uniqueProjects]);

  useEffect(() => {
    const handleProjectChange = (event: Event) => {
      const { projectId } = (event as CustomEvent<{ projectId?: string }>).detail ?? {};
      if (isKnownProject(uniqueProjects, projectId ?? null)) {
        setSelectedProjectId(projectId ?? null);
      }
    };

    window.addEventListener(PROJECT_CHANGE_EVENT, handleProjectChange);
    return () => window.removeEventListener(PROJECT_CHANGE_EVENT, handleProjectChange);
  }, [uniqueProjects]);

  function handleProjectChange(e: React.ChangeEvent<HTMLSelectElement>) {
    const id = e.target.value;
    setSelectedProjectId(id);
    publishProjectSelection(id);
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
          disabled={uniqueProjects.length === 0}
        >
          {uniqueProjects.map((p) => (
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
