"use client";

import { Bell, Leaf, Search } from "lucide-react";
import type { CurrentUser, Project } from "../../lib/types";
import { useState } from "react";

export default function Topbar({ projects, user }: { projects: Project[]; user: CurrentUser }) {
  const [searchQuery, setSearchQuery] = useState("");

  return (
    <header className="topbar">
      <div className="topbar-brand">
        <Leaf size={24} aria-hidden="true" />
        <span>HandoverOS</span>
      </div>
      <label className="project-select">
        <span className="sr-only">Project</span>
        <select defaultValue={projects[0]?.id} aria-label="Project">
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
      <div className="avatar" title={user.name}>
        {user.initials}
      </div>
    </header>
  );
}
