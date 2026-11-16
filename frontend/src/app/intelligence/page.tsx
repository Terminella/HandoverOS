"use client";

import Link from "next/link";
import {
  ArrowRight,
  CheckCircle2,
  FileText,
  FolderKanban,
  History,
  MessageSquareText,
  ShieldAlert,
  Sparkles,
  TriangleAlert,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import StatTiles from "../../components/dashboard/StatTiles";
import StatusChip from "../../components/ui/StatusChip";
import { apiRequest, getLlmStatus, getStoredToken } from "../../lib/api";
import { computeMetrics, countKind } from "../../lib/metrics";
import {
  PROJECT_CHANGE_EVENT,
  PROJECT_STORAGE_KEY,
  deduplicateProjects,
} from "../../lib/project-selection";
import type {
  BackendKnowledgeItem,
  BackendProject,
  BackendSource,
  KnowledgeItem,
  LlmStatus,
  Source,
} from "../../lib/types";
import {
  mapBackendKnowledgeItem,
  mapBackendSource,
} from "../../lib/types";

function CapabilityCard({
  icon: Icon,
  title,
  description,
}: {
  icon: typeof History;
  title: string;
  description: string;
}) {
  return (
    <li className="knowledge-card">
      <span className="row-icon tone-pending" aria-hidden="true">
        <Icon size={19} />
      </span>
      <div className="row-text">
        <p className="row-title">{title}</p>
        <p className="muted">{description}</p>
      </div>
      <span className="chip chip-pending">Not available</span>
    </li>
  );
}

function SourceRow({ source }: { source: Source }) {
  return (
    <li className="source-card">
      <div className="source-card-icon" aria-hidden="true">
        <FileText size={19} />
      </div>
      <div className="row-text">
        <p className="row-title">{source.name}</p>
        <p className="muted source-meta">
          <span className="source-type-label">{source.type}</span>
        </p>
      </div>
      <Link href="/sources" className="source-view-button">
        Manage sources
      </Link>
    </li>
  );
}

function KnowledgeRow({ item }: { item: KnowledgeItem }) {
  const humanReview = item.reviewed ? "Recorded" : "Not reviewed";

  return (
    <li className="knowledge-card">
      <span
        className={`row-icon tone-${item.status}`}
        aria-hidden="true"
      >
        {item.status === "verified" ? (
          <CheckCircle2 size={18} />
        ) : (
          <TriangleAlert size={18} />
        )}
      </span>
      <div className="row-text">
        <p className="row-title">{item.title}</p>
        <p className="muted knowledge-summary">{item.summary}</p>
        <p className="knowledge-kind">
          {item.kind.replace(/_/g, " ")} · {item.sourceIds.length} evidence reference
          {item.sourceIds.length === 1 ? "" : "s"}
        </p>
        <p className="muted" style={{ marginTop: 5 }}>
          Human review: {humanReview}
        </p>
      </div>
      <StatusChip status={item.status} />
    </li>
  );
}

export default function IntelligenceWorkspacePage() {
  const [projects, setProjects] = useState<BackendProject[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(null);
  const [sources, setSources] = useState<Source[]>([]);
  const [knowledgeItems, setKnowledgeItems] = useState<KnowledgeItem[]>([]);
  const [llmStatus, setLlmStatus] = useState<LlmStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [projectDataLoading, setProjectDataLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [projectDataError, setProjectDataError] = useState<string | null>(null);
  const [llmStatusError, setLlmStatusError] = useState<string | null>(null);

  const token = getStoredToken() ?? undefined;

  useEffect(() => {
    const syncSelectedProject = () => {
      setSelectedProjectId(localStorage.getItem(PROJECT_STORAGE_KEY));
    };

    const handleProjectChange = (event: Event) => {
      const customEvent = event as CustomEvent<{ projectId?: string }>;
      setSelectedProjectId(customEvent.detail?.projectId || null);
    };

    syncSelectedProject();
    window.addEventListener(PROJECT_CHANGE_EVENT, handleProjectChange);
    window.addEventListener("storage", syncSelectedProject);

    return () => {
      window.removeEventListener(PROJECT_CHANGE_EVENT, handleProjectChange);
      window.removeEventListener("storage", syncSelectedProject);
    };
  }, []);

  useEffect(() => {
    let mounted = true;

    async function loadProjects() {
      try {
        setLoading(true);
        setError(null);
        const response = await apiRequest<BackendProject[]>("/projects", token);
        if (!mounted) return;

        const availableProjects = deduplicateProjects(response);
        setProjects(availableProjects);

        const storedProjectId = localStorage.getItem(PROJECT_STORAGE_KEY);
        if (
          !storedProjectId ||
          !availableProjects.some((project) => project.id === storedProjectId)
        ) {
          setSelectedProjectId(null);
        }
      } catch (err) {
        if (mounted) {
          setError(err instanceof Error ? err.message : "Unable to load projects.");
        }
      } finally {
        if (mounted) setLoading(false);
      }
    }

    loadProjects();
    return () => {
      mounted = false;
    };
  }, [token]);

  useEffect(() => {
    let mounted = true;

    async function loadProjectData() {
      if (!selectedProjectId) {
        setSources([]);
        setKnowledgeItems([]);
        setProjectDataError(null);
        setProjectDataLoading(false);
        return;
      }

      try {
        setProjectDataLoading(true);
        setProjectDataError(null);
        setSources([]);
        setKnowledgeItems([]);

        const [sourceResponse, knowledgeResponse] = await Promise.all([
          apiRequest<BackendSource[]>(
            `/sources/${encodeURIComponent(selectedProjectId)}`,
            token,
          ),
          apiRequest<BackendKnowledgeItem[]>(
            `/knowledge/${encodeURIComponent(selectedProjectId)}`,
            token,
          ),
        ]);

        if (mounted) {
          setSources(sourceResponse.map(mapBackendSource));
          setKnowledgeItems(knowledgeResponse.map(mapBackendKnowledgeItem));
        }
      } catch (err) {
        if (mounted) {
          setProjectDataError(
            err instanceof Error
              ? err.message
              : "Unable to load this project’s Intelligence data.",
          );
        }
      } finally {
        if (mounted) setProjectDataLoading(false);
      }
    }

    loadProjectData();
    return () => {
      mounted = false;
    };
  }, [selectedProjectId, token]);

  useEffect(() => {
    let mounted = true;

    async function loadModelStatus() {
      try {
        setLlmStatusError(null);
        const response = await getLlmStatus(token);
        if (mounted) setLlmStatus(response);
      } catch (err) {
        if (mounted) {
          setLlmStatus(null);
          setLlmStatusError(
            err instanceof Error ? err.message : "Model status is unavailable.",
          );
        }
      }
    }

    loadModelStatus();
    return () => {
      mounted = false;
    };
  }, [token]);

  const project = useMemo(
    () => projects.find((candidate) => candidate.id === selectedProjectId) ?? null,
    [projects, selectedProjectId],
  );
  const metrics = computeMetrics(knowledgeItems);

  if (loading) {
    return (
      <section className="card placeholder" role="status" aria-live="polite">
        <h1 className="card-title">Loading Intelligence workspace...</h1>
        <p className="muted">Connecting to HandoverOS project data.</p>
      </section>
    );
  }

  if (error) {
    return (
      <section className="card placeholder" role="alert">
        <h1 className="card-title">Unable to load Intelligence workspace</h1>
        <p className="muted">{error}</p>
      </section>
    );
  }

  if (projects.length === 0) {
    return (
      <section className="card placeholder">
        <h1 className="card-title">No projects available</h1>
        <p className="muted">Create or join a project before opening Intelligence.</p>
        <Link href="/projects" className="action-btn">
          View projects
        </Link>
      </section>
    );
  }

  if (!project) {
    return (
      <section className="card placeholder">
        <h1 className="card-title">Select a project</h1>
        <p className="muted">
          Choose a project in the Topbar to view its sources and extracted knowledge.
        </p>
        <Link href="/projects" className="action-btn">
          Choose project
        </Link>
      </section>
    );
  }

  return (
    <div style={{ display: "grid", gap: 16 }}>
      <section className="card section-card" aria-labelledby="intelligence-title">
        <div className="card-head">
          <div>
            <p className="eyebrow">Project Intelligence</p>
            <h1 id="intelligence-title" className="card-title">
              {project.name}
            </h1>
            <p className="muted">
              Review the project’s existing sources and extracted knowledge.
            </p>
          </div>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            <Link href="/intelligence/reconstruct" className="action-btn">
              <Sparkles size={16} aria-hidden="true" />
              Reconstruct
            </Link>
            <Link href="/handovers/create" className="action-btn">
              Prepare handover
              <ArrowRight size={16} aria-hidden="true" />
            </Link>
          </div>
        </div>

        <nav className="settings-tabs" aria-label="Intelligence workspace sections">
          <a className="tab-btn tab-active" href="#overview">Overview</a>
          <a className="tab-btn" href="#sources">Sources</a>
          <a className="tab-btn" href="#knowledge">Knowledge</a>
          <a className="tab-btn" href="#reconstruction">Reconstruction</a>
          <a className="tab-btn" href="#handover">Handover</a>
        </nav>
      </section>

      <section id="overview" aria-labelledby="overview-title">
        <div className="card-head">
          <div>
            <h2 id="overview-title" className="card-title">Overview</h2>
            <p className="muted">Current project data available through the existing APIs.</p>
          </div>
        </div>

        {projectDataLoading ? (
          <section className="card placeholder" role="status" aria-live="polite">
            <p className="muted">Loading sources and knowledge...</p>
          </section>
        ) : projectDataError ? (
          <section className="card placeholder" role="alert">
            <p className="muted">{projectDataError}</p>
          </section>
        ) : (
          <>
            <StatTiles
              sources={sources.length}
              decisions={countKind(knowledgeItems, "decision")}
              tasks={countKind(knowledgeItems, "task")}
              blockers={countKind(knowledgeItems, "blocker")}
              unresolved={countKind(knowledgeItems, "unresolved")}
            />
            <div className="grid-2a" style={{ marginTop: 16 }}>
              <section className="card">
                <div className="card-head">
                  <div>
                    <h3 className="card-title">Knowledge status</h3>
                    <p className="muted">Evidence and review states are shown separately.</p>
                  </div>
                </div>
                <ul className="rows">
                  <li className="row-item"><span className="row-text">Total findings</span><strong>{metrics.total}</strong></li>
                  <li className="row-item"><span className="row-text">Evidence verified</span><strong>{metrics.verified}</strong></li>
                  <li className="row-item"><span className="row-text">Needs verification</span><strong>{metrics.needsVerification}</strong></li>
                  <li className="row-item"><span className="row-text">Contradictions</span><strong>{metrics.conflicting}</strong></li>
                </ul>
              </section>
              <section className="card">
                <div className="card-head">
                  <div>
                    <h3 className="card-title">Current model</h3>
                    <p className="muted">Reported by the existing system status endpoint.</p>
                  </div>
                </div>
                {llmStatus ? (
                  <ul className="rows">
                    <li className="row-item"><span className="row-text">Provider</span><strong>{llmStatus.provider || "Unknown"}</strong></li>
                    <li className="row-item"><span className="row-text">Model</span><strong>{llmStatus.model || llmStatus.ollama_model || "Not selected"}</strong></li>
                  </ul>
                ) : (
                  <p className="muted">{llmStatusError || "Model status is unavailable."}</p>
                )}
              </section>
            </div>
          </>
        )}
      </section>

      <section id="sources" className="card section-card" aria-labelledby="sources-title">
        <div className="card-head">
          <div>
            <h2 id="sources-title" className="card-title">Sources</h2>
            <p className="muted">Existing project sources used by reconstruction.</p>
          </div>
          <Link href="/sources" className="link-btn">Manage sources <ArrowRight size={16} aria-hidden="true" /></Link>
        </div>
        {sources.length === 0 ? (
          <p className="muted">No sources are available for this project yet.</p>
        ) : (
          <ul className="section-list source-list">
            {sources.map((source) => <SourceRow key={source.id} source={source} />)}
          </ul>
        )}
      </section>

      <section id="knowledge" className="card section-card" aria-labelledby="knowledge-title">
        <div className="card-head">
          <div>
            <h2 id="knowledge-title" className="card-title">Knowledge</h2>
            <p className="muted">Extracted items with their current evidence and human-review states.</p>
          </div>
        </div>
        {knowledgeItems.length === 0 ? (
          <p className="muted">No findings yet. Run reconstruction after sources are available.</p>
        ) : (
          <ul className="section-list knowledge-list">
            {knowledgeItems.map((item) => <KnowledgeRow key={item.id} item={item} />)}
          </ul>
        )}
      </section>

      <section id="reconstruction" className="card section-card" aria-labelledby="reconstruction-title">
        <div className="card-head">
          <div>
            <h2 id="reconstruction-title" className="card-title">Reconstruction</h2>
            <p className="muted">Use the existing synchronous reconstruction workflow.</p>
          </div>
          <Link href="/intelligence/reconstruct" className="action-btn">
            Run reconstruction <ArrowRight size={16} aria-hidden="true" />
          </Link>
        </div>
        <p className="muted">
          The current API processes the project’s existing sources and reports a completed result or an error. This workspace does not claim progress tracking, cancellation, background runs, or run history.
        </p>
      </section>

      <section id="handover" className="card section-card" aria-labelledby="handover-title">
        <div className="card-head">
          <div>
            <h2 id="handover-title" className="card-title">Handover</h2>
            <p className="muted">Continue with the existing handover draft and approval workflow.</p>
          </div>
          <Link href="/handovers/create" className="action-btn">
            Open handover workflow <ArrowRight size={16} aria-hidden="true" />
          </Link>
        </div>
        <p className="muted">
          Handover generation remains separate from this read-only Intelligence overview and continues to use the existing project workflow.
        </p>
      </section>

      <section className="card section-card" aria-labelledby="future-title">
        <div className="card-head">
          <div>
            <h2 id="future-title" className="card-title">Future Intelligence capabilities</h2>
            <p className="muted">These capabilities need backend contracts and persistence before they can be enabled.</p>
          </div>
        </div>
        <ul className="section-list knowledge-list">
          <CapabilityCard icon={ShieldAlert} title="Individual finding review" description="Approve, correct, reject, or request clarification for one finding." />
          <CapabilityCard icon={History} title="Persistent reconstruction runs" description="Run history, progress, cancellation, and retry state are not available yet." />
          <CapabilityCard icon={TriangleAlert} title="Contradiction management" description="Contradiction details and resolution actions are not exposed by the current API." />
          <CapabilityCard icon={MessageSquareText} title="Contextual AI chat" description="Project-aware chat and citation-backed answers are not implemented yet." />
        </ul>
      </section>

      <p className="muted" style={{ display: "flex", alignItems: "center", gap: 8 }}>
        <FolderKanban size={16} aria-hidden="true" />
        Project context comes from the existing Topbar selection. No project IDs or mock results are hardcoded.
      </p>
    </div>
  );
}
