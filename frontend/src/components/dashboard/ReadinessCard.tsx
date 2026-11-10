interface Props {
  readiness: number;
  verified: number;
  needsVerification: number;
  conflicting: number;
  pending: number;
}

const R = 52;
const C = 2 * Math.PI * R;

export default function ReadinessCard({ readiness, verified, needsVerification, conflicting, pending }: Props) {
  const legend = [
    { label: "Verified", count: verified, cls: "dot-ok" },
    { label: "Needs verification", count: needsVerification, cls: "dot-warn" },
    { label: "Conflicting", count: conflicting, cls: "dot-danger" },
    { label: "Pending", count: pending, cls: "dot-muted" },
  ];

  return (
    <section className="card" aria-labelledby="readiness-title">
      <div className="readiness">
        <svg viewBox="0 0 120 120" className="ring" role="img" aria-label={`Handover readiness ${readiness} percent`}>
          <circle cx="60" cy="60" r={R} className="ring-track" />
          <circle
            cx="60"
            cy="60"
            r={R}
            className="ring-fill"
            strokeDasharray={`${(C * readiness) / 100} ${C}`}
            transform="rotate(-90 60 60)"
          />
          <text x="60" y="66" textAnchor="middle" className="ring-text">
            {readiness}%
          </text>
        </svg>
        <div>
          <h2 id="readiness-title" className="card-title">Handover Readiness</h2>
          <p className="muted">Share of items verified and reviewed by a person.</p>
          <ul className="legend">
            {legend.map(({ label, count, cls }) => (
              <li key={label}>
                <span className={`dot ${cls}`} aria-hidden="true" />
                {label} ({count})
              </li>
            ))}
          </ul>
        </div>
      </div>
    </section>
  );
}
