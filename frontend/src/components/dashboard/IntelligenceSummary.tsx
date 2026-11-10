import { ArrowLeftRight, ArrowRight, Check, Sparkles, TriangleAlert } from "lucide-react";
import Link from "next/link";
import { KIND_LABEL } from "../../lib/labels";
import type { ItemStatus, KnowledgeItem } from "../../lib/types";
import StatusChip from "../ui/StatusChip";

const ROW_ICONS = {
  verified: Check,
  needs_verification: TriangleAlert,
  conflicting: ArrowLeftRight,
  pending: Sparkles,
} as const;

export default function IntelligenceSummary({ items }: { items: KnowledgeItem[] }) {
  return (
    <section className="card" aria-labelledby="intel-title">
      <div className="card-head">
        <div>
          <h2 id="intel-title" className="card-title">Intelligence Summary</h2>
          <p className="muted">Extracted insights with evidence and status.</p>
        </div>
        <Link href="/intelligence" className="link-btn">
          View All <ArrowRight size={16} aria-hidden="true" />
        </Link>
      </div>
      {items.length === 0 ? (
        <p className="muted">No findings yet. Connect a source to begin.</p>
      ) : (
        <ul className="rows">
          {items.map((item) => {
            const Icon = ROW_ICONS[item.status as ItemStatus];
            const title = item.status === "conflicting" ? "Contradiction" : KIND_LABEL[item.kind];
            return (
              <li key={item.id} className="row-item">
                <span className={`row-icon tone-${item.status}`}>
                  <Icon size={20} aria-hidden="true" />
                </span>
                <div className="row-text">
                  <p className="row-title">{title}</p>
                  <p className="muted">{item.summary}</p>
                </div>
                <StatusChip status={item.status} />
              </li>
            );
          })}
        </ul>
      )}
    </section>
  );
}
