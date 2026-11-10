import { Check, Layers, Lock, Pencil, Plug, Search, Send } from "lucide-react";
import type { Stage, StageId } from "../../lib/types";

const STAGE_ICONS = {
  connect: Plug,
  reconstruct: Layers,
  verify: Search,
  review: Pencil,
  handover: Send,
} as const;

interface Props {
  stages: Stage[];
  current: StageId;
  visibleTo: string;
  draftVersion: string;
}

export default function PipelineCard({ stages, current, visibleTo, draftVersion }: Props) {
  const currentIndex = stages.findIndex((s) => s.id === current);

  return (
    <section className="card" aria-labelledby="pipeline-title">
      <div className="card-head">
        <div>
          <h2 id="pipeline-title" className="card-title">Handover Pipeline</h2>
          <p className="muted">From connection to a shareable handover. Draft {draftVersion}.</p>
        </div>
        <span className="pill">
          <Lock size={14} aria-hidden="true" />
          Visible to: <strong>{visibleTo}</strong>
        </span>
      </div>
      <ol className="steps">
        {stages.map((stage, i) => {
          const state = i < currentIndex ? "done" : i === currentIndex ? "current" : "todo";
          const Icon = state === "done" ? Check : STAGE_ICONS[stage.id];
          return (
            <li key={stage.id} className={`step step-${state}`} aria-current={state === "current" ? "step" : undefined}>
              <span className="step-icon">
                <Icon size={20} aria-hidden="true" />
              </span>
              <span className="step-label">{stage.label}</span>
              <span className="step-hint">{stage.hint}</span>
              <span className="sr-only">{state === "done" ? "(completed)" : state === "current" ? "(in progress)" : "(not started)"}</span>
            </li>
          );
        })}
      </ol>
    </section>
  );
}
