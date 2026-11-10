import { notFound } from "next/navigation";
import { projects, sources, items, handovers, teamMembers } from "../../lib/mock-data";
import { STAGES } from "../../lib/stages";
import { STATUS_LABEL } from "../../lib/labels";
import StatusChip from "../../components/ui/StatusChip";
import type { StageId } from "../../lib/types";

const SECTIONS: Record<string, { title: string; subtitle?: string }> = {
  projects: { title: "Projects", subtitle: "Connected project workspaces" },
  sources: { title: "Sources", subtitle: "Ingested documents and repositories" },
  intelligence: { title: "Intelligence", subtitle: "Extracted knowledge items" },
  handovers: { title: "Handovers" },
  team: { title: "Team" },
  settings: { title: "Settings" },
};

export const dynamicParams = false;

export function generateStaticParams() {
  return Object.keys(SECTIONS).map((section) => ({ section }));
}

export default async function SectionPage({ params }: { params: Promise<{ section: string }> }) {
  const { section } = await params;
  const config = SECTIONS[section];
  if (!config) notFound();

  if (section === "projects") {
    return (
      <section className="card placeholder">
        <div className="card-head">
          <div>
            <h1 className="card-title">{config.title}</h1>
            <p className="muted">{config.subtitle}</p>
          </div>
        </div>
        <ul className="rows">
          {projects.map((p) => {
            const stage = STAGES.find((s) => s.id === p.stage);
            return (
              <li key={p.id} className="row-item">
                <div className="row-text">
                  <p className="row-title">{p.name}</p>
                  <p className="muted">
                    {stage?.label} &middot; {p.visibleTo} &middot; Draft {p.draftVersion}
                  </p>
                </div>
              </li>
            );
          })}
          {projects.length === 0 && (
            <li className="row-item">
              <p className="muted">No projects yet.</p>
            </li>
          )}
        </ul>
      </section>
    );
  }

  if (section === "sources") {
    return (
      <section className="card placeholder">
        <div className="card-head">
          <div>
            <h1 className="card-title">{config.title}</h1>
            <p className="muted">{config.subtitle}</p>
          </div>
        </div>
        <ul className="rows">
          {sources.map((s) => (
            <li key={s.id} className="row-item">
              <div className="row-text">
                <p className="row-title">{s.name}</p>
                <p className="muted">{s.type}</p>
              </div>
            </li>
          ))}
          {sources.length === 0 && (
            <li className="row-item">
              <p className="muted">No sources yet.</p>
            </li>
          )}
        </ul>
      </section>
    );
  }

  if (section === "intelligence") {
    return (
      <section className="card placeholder">
        <div className="card-head">
          <div>
            <h1 className="card-title">{config.title}</h1>
            <p className="muted">{config.subtitle}</p>
          </div>
        </div>
        {items.length === 0 ? (
          <p className="muted">No findings yet. Connect a source to begin.</p>
        ) : (
          <ul className="rows">
            {items.map((item) => (
              <li key={item.id} className="row-item">
                <span className={`row-icon tone-${item.status}`} />
                <div className="row-text">
                  <p className="row-title">{item.title}</p>
                  <p className="muted">{item.summary}</p>
                </div>
                <StatusChip status={item.status} />
              </li>
            ))}
          </ul>
        )}
      </section>
    );
  }

  if (section === "handovers") {
    return (
      <section className="card placeholder">
        <div className="card-head">
          <div>
            <h1 className="card-title">{config.title}</h1>
            <p className="muted">Generated handover versions for the selected project.</p>
          </div>
        </div>
        {handovers.length === 0 ? (
          <p className="muted">No handovers yet. Generate one after review.</p>
        ) : (
          <ul className="rows">
            {handovers.map((h) => (
              <li key={h.id} className="row-item">
                <div className="row-text">
                  <p className="row-title">{`Handover ${h.version}`}</p>
                  <p className="muted">{h.status} &middot; prepared by {h.preparedBy} &middot; {h.generatedAt}</p>
                </div>
                <span className={`chip chip-${h.status}`}>{h.status.replace(/_/g, " ")}</span>
              </li>
            ))}
          </ul>
        )}
      </section>
    );
  }

  if (section === "team") {
    return (
      <section className="card placeholder">
        <div className="card-head">
          <div>
            <h1 className="card-title">{config.title}</h1>
            <p className="muted">Project team members and their roles.</p>
          </div>
        </div>
        {teamMembers.length === 0 ? (
          <p className="muted">No team members yet.</p>
        ) : (
          <ul className="rows">
            {teamMembers.map((m) => (
              <li key={m.id} className="row-item">
                <div className="row-text">
                  <p className="row-title">{m.name}</p>
                  <p className="muted">{m.role}</p>
                </div>
                <span className="avatar" style={{ width: 32, height: 32, fontSize: "0.8rem" }} title={m.name}>
                  {m.initials}
                </span>
              </li>
            ))}
          </ul>
        )}
      </section>
    );
  }

  if (section === "settings") {
    return (
      <section className="card placeholder">
        <div className="card-head">
          <div>
            <h1 className="card-title">{config.title}</h1>
            <p className="muted">Application preferences and appearance.</p>
          </div>
        </div>
        <p className="muted">Use the theme toggle in the sidebar to switch between light and dark mode.</p>
      </section>
    );
  }

  return (
    <section className="card placeholder">
      <h1 className="card-title">{config.title}</h1>
      <p className="muted">This screen is planned and not built yet.</p>
    </section>
  );
}
