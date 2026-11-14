"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { apiRequest, getStoredToken } from "../../lib/api";
import StatusChip from "../../components/ui/StatusChip";
import type {
  BackendProject,
  BackendKnowledgeItem,
  BackendSource,
  Handover,
  KnowledgeItem,
  Source,
} from "../../lib/types";
import { mapBackendKnowledgeItem, mapBackendSource } from "../../lib/types";

const SECTIONS: Record<string, { title: string; subtitle?: string }> = {
  projects: { title: "Projects", subtitle: "Connected project workspaces" },
  sources: { title: "Sources", subtitle: "Ingested documents and repositories" },
  intelligence: { title: "Intelligence", subtitle: "Extracted knowledge items" },
  handovers: { title: "Handovers" },
  team: { title: "Team", subtitle: "Project members and their roles" },
  settings: { title: "Settings", subtitle: "Application preferences and administration" },
};

type SectionParams = { section: string };

function ProjectRow({ project, onSelect }: { project: BackendProject; onSelect: (id: string) => void }) {
  return (
    <li key={project.id} className="row-item" onClick={() => onSelect(project.id)}>
      <div className="row-text">
        <p className="row-title">{project.name}</p>
        <p className="muted">
          {project.description || "No description"} &middot; {project.status}
        </p>
      </div>
    </li>
  );
}

function SourceRow({ source }: { source: Source }) {
  return (
    <li key={source.id} className="row-item">
      <div className="row-text">
        <p className="row-title">{source.name}</p>
        <p className="muted">{source.type}</p>
      </div>
    </li>
  );
}

function KnowledgeRow({ item }: { item: KnowledgeItem }) {
  return (
    <li key={item.id} className="row-item">
      <span className={`row-icon tone-${item.status}`} />
      <div className="row-text">
        <p className="row-title">{item.title}</p>
        <p className="muted">{item.summary}</p>
      </div>
      <StatusChip status={item.status} />
    </li>
  );
}

function HandoverRow({ handover }: { handover: Handover }) {
  return (
    <li key={handover.id} className="row-item">
      <div className="row-text">
        <p className="row-title">Handover {handover.version}</p>
        <p className="muted">
          {handover.status} &middot; prepared by {handover.preparedBy} &middot;
          {handover.generatedAt}
        </p>
      </div>
      <span className={`chip chip-${handover.status}`}>
        {handover.status.replace(/_/g, " ")}
      </span>
    </li>
  );
}

function TeamRow({ user }: { user: { id: string; name: string; email: string } }) {
  return (
    <li key={user.id} className="row-item">
      <div className="row-text">
        <p className="row-title">{user.name}</p>
        <p className="muted">{user.email}</p>
      </div>
    </li>
  );
}

export default function SectionPage({ params }: { params: Promise<SectionParams> }) {
  const router = useRouter();
  const [section, setSection] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    params.then((p) => {
      if (mounted) setSection(p.section);
    });
    return () => { mounted = false; };
  }, [params]);

  const [projects, setProjects] = useState<BackendProject[]>([]);
  const [sources, setSources] = useState<Source[]>([]);
  const [knowledgeItems, setKnowledgeItems] = useState<KnowledgeItem[]>([]);
  const [handovers, setHandovers] = useState<Handover[]>([]);
  const [teamMembers, setTeamMembers] = useState<{ id: string; name: string; email: string }[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(null);

  const config = section ? SECTIONS[section] : undefined;

  const token = getStoredToken() ?? undefined;

  useEffect(() => {
    let mounted = true;
    async function loadSectionData() {
      try {
        setLoading(true);
        setError(null);

        if (section === "projects") {
          const response = await apiRequest<BackendProject[]>("/projects", token);
          setProjects(response);
          if (response.length > 0) {
            setSelectedProjectId(response[0].id);
          }
        } else if (section === "sources" && selectedProjectId) {
          const response = await apiRequest<BackendSource[]>(`/sources/${selectedProjectId}`, token);
          setSources(response.map(mapBackendSource));
        } else if (section === "intelligence" && selectedProjectId) {
          const response = await apiRequest<BackendKnowledgeItem[]>(`/knowledge/${selectedProjectId}`, token);
          setKnowledgeItems(response.map(mapBackendKnowledgeItem));
        } else if (section === "handovers" && selectedProjectId) {
          const response = await apiRequest<Handover[]>(`/handovers/${selectedProjectId}`, token);
          setHandovers(response);
        } else if (section === "team") {
          const response = await apiRequest<{ id: string; name: string; email: string }[]>("/users", token);
          setTeamMembers(response);
        }
      } catch (err) {
        if (mounted) {
          setError(err instanceof Error ? err.message : "Failed to load data");
        }
      } finally {
        if (mounted) setLoading(false);
      }
    }

    loadSectionData();
    return () => { mounted = false; };
  }, [section, selectedProjectId, token]);

  if (!config) {
    return null;
  }

  if (loading) {
    return (
      <section className="card placeholder">
        <h1 className="card-title">Loading...</h1>
        <p className="muted">Fetching data from HandoverOS backend.</p>
      </section>
    );
  }

  if (error) {
    return (
      <section className="card placeholder">
        <h1 className="card-title">Unable to load data</h1>
        <p className="muted">{error}</p>
      </section>
    );
  }

  const sectionContent = () => {
    if (section === "projects") {
      return (
        <>
          <div className="card-head">
            <div>
              <h1 className="card-title">{config.title}</h1>
              <p className="muted">{config.subtitle}</p>
            </div>
            <button
              type="button"
              className="action-btn"
              onClick={() => router.push("/projects/create")}
            >
              Create project
            </button>
          </div>
          <ul className="rows">
            {projects.length === 0 ? (
              <li className="row-item">
                <p className="muted">No projects yet. Create a project to begin.</p>
              </li>
            ) : (
              projects.map((p) => (
                <ProjectRow key={p.id} project={p} onSelect={setSelectedProjectId} />
              ))
            )}
          </ul>
        </>
      );
    }

    if (section === "sources") {
      return (
        <>
          <div className="card-head">
            <div>
              <h1 className="card-title">{config.title}</h1>
              <p className="muted">{config.subtitle}</p>
            </div>
            {!selectedProjectId ? null : (
              <a href="/sources/upload" className="action-btn">Upload source</a>
            )}
          </div>
          {!selectedProjectId ? (
            <p className="muted">Select a project to view its sources.</p>
          ) : (
            <ul className="rows">
              {sources.length === 0 ? (
                <li className="row-item">
                  <p className="muted">No sources for this project yet.</p>
                </li>
              ) : null}
              {sources.map((s) => (
                <SourceRow key={s.id} source={s} />
              ))}
            </ul>
          )}
        </>
      );
    }

    if (section === "intelligence") {
      return (
        <>
          <div className="card-head">
            <div>
              <h1 className="card-title">{config.title}</h1>
              <p className="muted">{config.subtitle}</p>
            </div>
            {!selectedProjectId ? null : (
              <a href="/intelligence/reconstruct" className="action-btn">Run reconstruction</a>
            )}
          </div>
          {!selectedProjectId ? (
            <p className="muted">Select a project to view extracted knowledge.</p>
          ) : (
            knowledgeItems.length === 0 ? (
              <p className="muted">No findings yet. Connect a source and run reconstruction to begin.</p>
            ) : (
              <ul className="rows">
                {knowledgeItems.map((item) => <KnowledgeRow key={item.id} item={item} />)}
              </ul>
            )
          )}
        </>
      );
    }

    if (section === "handovers") {
      return (
        <>
          <div className="card-head">
            <div>
              <h1 className="card-title">{config.title}</h1>
              <p className="muted">Generated handover versions for the selected project.</p>
            </div>
            {!selectedProjectId ? null : (
              <a href="/handovers/create" className="action-btn">Generate handover</a>
            )}
          </div>
          {!selectedProjectId ? (
            <p className="muted">Select a project to view its handovers.</p>
          ) : (
            handovers.length === 0 ? (
              <p className="muted">No handovers yet. Generate one after knowledge verification.</p>
            ) : (
              <ul className="rows">
                {handovers.map((h) => <HandoverRow key={h.id} handover={h} />)}
              </ul>
            )
          )}
        </>
      );
    }

    if (section === "team") {
      return (
        <>
          <div className="card-head">
            <div>
              <h1 className="card-title">{config.title}</h1>
              <p className="muted">{config.subtitle}</p>
            </div>
          </div>
          {teamMembers.length === 0 ? (
            <p className="muted">No team members found.</p>
          ) : (
            <ul className="rows">
              {teamMembers.map((m) => <TeamRow key={m.id} user={m} />)}
            </ul>
          )}
        </>
      );
    }

    return null;
  };

  return (
    <section className="card">
      <div className="card-head">
        <div>
          <h1 className="card-title">{config.title}</h1>
          <p className="muted">{config.subtitle}</p>
        </div>
      </div>
      {sectionContent()}
    </section>
  );
}
