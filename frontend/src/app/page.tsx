import EvidencePanel from "../components/dashboard/EvidencePanel";
import IntelligenceSummary from "../components/dashboard/IntelligenceSummary";
import PipelineCard from "../components/dashboard/PipelineCard";
import ReadinessCard from "../components/dashboard/ReadinessCard";
import StatTiles from "../components/dashboard/StatTiles";
import { computeMetrics, countKind } from "../lib/metrics";
import { items, projects, sources } from "../lib/mock-data";
import { STAGES } from "../lib/stages";
import type { ItemStatus, KnowledgeItem } from "../lib/types";

export default function OverviewPage() {
  if (projects.length === 0) {
    return (
      <section className="card placeholder">
        <h1 className="card-title">No projects</h1>
        <p className="muted">No projects are available yet. Connect a source or create a project to begin.</p>
      </section>
    );
  }

  const project = projects[0];
  const m = computeMetrics(items);

  const first = (status: ItemStatus) => items.find((i) => i.status === status);
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
        <p className="demo-note">Showing synthetic demo data for {project.name}.</p>
        <svg viewBox="0 0 600 160" preserveAspectRatio="xMaxYMax meet" aria-hidden="true">
          <circle cx="400" cy="46" r="34" fill="var(--sun)" />
          <path d="M0 160 L130 70 L210 120 L320 40 L440 125 L520 85 L600 130 L600 160 Z" fill="var(--mtn-a)" />
          <path d="M120 160 L260 90 L340 130 L450 75 L600 150 L600 160 Z" fill="var(--mtn-b)" />
        </svg>
      </section>

      <StatTiles
        sources={sources.length}
        decisions={countKind(items, "decision")}
        tasks={countKind(items, "task")}
        blockers={countKind(items, "blocker")}
        unresolved={countKind(items, "unresolved")}
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
