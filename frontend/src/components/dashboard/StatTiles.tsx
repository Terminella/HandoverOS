import { CircleHelp, FileText, Layers, ListChecks, TriangleAlert } from "lucide-react";

interface Props {
  sources: number;
  decisions: number;
  tasks: number;
  blockers: number;
  unresolved: number;
}

export default function StatTiles({ sources, decisions, tasks, blockers, unresolved }: Props) {
  const tiles = [
    { label: "Sources", value: sources, hint: "Documents, code, notes", icon: FileText, tone: "ok" },
    { label: "Decisions", value: decisions, hint: "Key project decisions", icon: Layers, tone: "info" },
    { label: "Tasks", value: tasks, hint: "Actionable items", icon: ListChecks, tone: "info" },
    { label: "Blockers", value: blockers, hint: "Open issues", icon: TriangleAlert, tone: "warn" },
    { label: "Unresolved", value: unresolved, hint: "Need clarification", icon: CircleHelp, tone: "danger" },
  ] as const;

  return (
    <ul className="stats">
      {tiles.map(({ label, value, hint, icon: Icon, tone }) => (
        <li key={label} className="card stat">
          <span className={`stat-icon tone-${tone}`}>
            <Icon size={22} aria-hidden="true" />
          </span>
          <div>
            <p className="stat-value">
              {value} <span className="stat-label">{label}</span>
            </p>
            <p className="stat-hint">{hint}</p>
          </div>
        </li>
      ))}
    </ul>
  );
}
