import { ArrowLeftRight, ChartColumn, TriangleAlert } from "lucide-react";

interface Props {
  coverage: number;
  needsVerification: number;
  contradictions: number;
}

export default function EvidencePanel({ coverage, needsVerification, contradictions }: Props) {
  return (
    <section className="card" aria-labelledby="evidence-title">
      <h2 id="evidence-title" className="card-title">Evidence &amp; Uncertainty</h2>
      <p className="muted">Traceability and reliability of extracted knowledge.</p>
      <ul className="rows">
        <li className="row-item">
          <span className="row-icon tone-verified">
            <ChartColumn size={20} aria-hidden="true" />
          </span>
          <div className="row-text">
            <p className="row-title">Evidence Coverage</p>
            <div className="bar" role="progressbar" aria-label="Evidence coverage" aria-valuemin={0} aria-valuemax={100} aria-valuenow={coverage}>
              <div className="bar-fill" style={{ width: `${coverage}%` }} />
            </div>
          </div>
          <strong>{coverage}%</strong>
        </li>
        <li className="row-item">
          <span className="row-icon tone-needs_verification">
            <TriangleAlert size={20} aria-hidden="true" />
          </span>
          <p className="row-title row-text">Needs Verification</p>
          <strong>{needsVerification}</strong>
        </li>
        <li className="row-item">
          <span className="row-icon tone-conflicting">
            <ArrowLeftRight size={20} aria-hidden="true" />
          </span>
          <p className="row-title row-text">Contradictions</p>
          <strong>{contradictions}</strong>
        </li>
      </ul>
    </section>
  );
}
