"use client";

import { useEffect, useState } from "react";
import EvidencePanel from "../components/dashboard/EvidencePanel";
import IntelligenceSummary from "../components/dashboard/IntelligenceSummary";
import PipelineCard from "../components/dashboard/PipelineCard";
import ReadinessCard from "../components/dashboard/ReadinessCard";
import StatTiles from "../components/dashboard/StatTiles";
import { computeMetrics, countKind } from "../lib/metrics";
import { STAGES } from "../lib/stages";
import { apiRequest } from "../lib/api";
import { getStoredToken } from "../lib/api";
import type { BackendProject, BackendKnowledgeItem, BackendSource, ItemStatus, KnowledgeItem, Project, Source } from "../lib/types";
import { mapBackendKnowledgeItem, mapBackendProject, mapBackendSource } from "../lib/types";

export default function OverviewPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [knowledgeItems, setKnowledgeItems] = useState<KnowledgeItem[]>([]);
  const [sources, setSources] = useState<Source[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    async function loadData() {
      try {
        setLoading(true);
        const token = getStoredToken() ?? undefined;
        const response = await apiRequest<BackendProject[]>("/projects", token);
        if (mounted) {
          const mapped = response.map(mapBackendProject);
          setProjects(mapped);
          if (mapped.length > 0 && !selectedProjectId) {
            setSelectedProjectId(mapped[0].id);
          }
        }
      } catch (err) {
        if (mounted) {
          setError(err instanceof Error ? err.message : "Failed to load projects");
        }
      } finally {
        if (mounted) setLoading(false);
      }
    }
    loadData();
    return () => { mounted = false; };
  }, []);

  useEffect(() => {
    let mounted = true;
    async function loadProjectData() {
      if (!selectedProjectId) return;
      try {
        const token = getStoredToken() ?? undefined;
        const [knowledgeResponse, sourcesResponse] = await Promise.all([
          apiRequest<BackendKnowledgeItem[]>(`/knowledge/${selectedProjectId}`, token),
          apiRequest<BackendSource[]>(`/sources/${selectedProjectId}`, token),
        ]);
        if (mounted) {
          setKnowledgeItems(knowledgeResponse.map(mapBackendKnowledgeItem));
          setSources(sourcesResponse.map(mapBackendSource));
        }
      } catch (err) {
        if (mounted) {
          console.error("Failed to load project data", err);
        }
      }
    }
    loadProjectData();
    return () => { mounted = false; };
  }, [selectedProjectId]);

  if (loading) {
    return (
      <section className="card placeholder">
        <h1 className="card-title">Loading workspace...</h1>
        <p className="muted">Connecting to HandoverOS backend.</p>
      </section>
    );
  }

  if (error) {
    return (
      <section className="card placeholder">
        <h1 className="card-title">Unable to load workspace</h1>
        <p className="muted">{error}</p>
        <p className="muted">Ensure the backend is running at http://127.0.0.1:8000 and try again.</p>
      </section>
    );
  }

  if (projects.length === 0) {
    return (
      <section className="card placeholder">
        <h1 className="card-title">No projects</h1>
        <p className="muted">No projects are available yet. Create a project to begin.</p>
      </section>
    );
  }

  const project = projects.find((p) => p.id === selectedProjectId) || projects[0];
  const m = computeMetrics(knowledgeItems);

  const first = (status: ItemStatus) => knowledgeItems.find((i) => i.status === status);
  const highlights = [first("verified"), first("needs_verification"), first("conflicting")].filter(
    (i): i is KnowledgeItem => i !== undefined,
  );

  return (
    <>
      <section className="hero" aria-labelledby="hero-title">
        <p className="eyebrow">Project workspace</p>
        <h1 id="hero-title">
          Keep the work <em>moving.</em>
        </h1>
        <p className="lead">Reconstruct context, verify evidence and deliver a seamless handover.</p>
        <p className="demo-note">Project: {project.name}</p>
        <svg viewBox="0 0 600 160" preserveAspectRatio="xMaxYMax meet" aria-hidden="true">
          <circle cx="400" cy="46" r="34" fill="var(--sun)" />
          <path d="M0 160 L130 70 L210 120 L320 40 L440 125 L520 85 L600 130 L600 160 Z" fill="var(--mtn-a)" />
          <path d="M120 160 L260 90 L340 130 L450 75 L600 150 L600 160 Z" fill="var(--mtn-b)" />
        </svg>
      </section>

      <StatTiles
        sources={sources.length}
        decisions={countKind(knowledgeItems, "decision")}
        tasks={countKind(knowledgeItems, "task")}
        blockers={countKind(knowledgeItems, "blocker")}
        unresolved={countKind(knowledgeItems, "unresolved")}
      />

      <div className="grid-2a">
        <ReadinessCard
          readiness={m.readiness}
          verified={m.verified}
          needsVerification={m.needsVerification}
          conflicting={m.conflicting}
          pending={m.pending}
        />
        <PipelineCard
          stages={STAGES}
          current={project.stage}
          visibleTo={project.visibleTo}
          draftVersion={project.draftVersion}
        />
      </div>

      <div className="grid-2b">
        <IntelligenceSummary items={highlights} />
        <EvidencePanel
          coverage={m.evidenceCoverage}
          needsVerification={m.needsVerification}
          contradictions={m.conflicting}
        />
      </div>
    </>
  );
}
