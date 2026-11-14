"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { apiPost, getStoredToken } from "../../../lib/api";

export default function ReconstructPage() {
  const router = useRouter();
  const [projectId, setProjectId] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<{
    claims_extracted: number;
    claims_verified: number;
    claims_unsupported: number;
    contradictions: number;
    knowledge_items_created: number;
    message: string;
  } | null>(null);

  const token = getStoredToken() ?? undefined;

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError("");
    setLoading(true);
    setResult(null);

    try {
      const res = await apiPost<{
        claims_extracted: number;
        claims_verified: number;
        claims_unsupported: number;
        contradictions: number;
        knowledge_items_created: number;
        message: string;
      }>("/knowledge/reconstruct", { project_id: projectId }, token);

      setResult(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Reconstruction failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="card">
      <div className="card-head">
        <div>
          <h1 className="card-title">Knowledge Reconstruction</h1>
          <p className="muted">Extract structured knowledge from ingested sources.</p>
        </div>
      </div>

      {error && <p className="auth-error" role="alert">{error}</p>}
      {result && (
        <div style={{ background: "var(--primary-soft)", border: "1px solid var(--border)", borderRadius: "8px", padding: 16, marginBottom: 20 }}>
          <h2 style={{ margin: 0, fontSize: "1rem", color: "var(--primary)" }}>{result.message}</h2>
          <ul className="rows" style={{ marginTop: 10 }}>
            <li className="row-item">
              <div className="row-text"><p className="row-title">Claims extracted</p></div>
              <strong>{result.claims_extracted}</strong>
            </li>
            <li className="row-item">
              <div className="row-text"><p className="row-title">Claims verified</p></div>
              <strong>{result.claims_verified}</strong>
            </li>
            <li className="row-item">
              <div className="row-text"><p className="row-title">Unsupported</p></div>
              <strong>{result.claims_unsupported}</strong>
            </li>
            <li className="row-item">
              <div className="row-text"><p className="row-title">Contradictions</p></div>
              <strong>{result.contradictions}</strong>
            </li>
            <li className="row-item">
              <div className="row-text"><p className="row-title">Knowledge items created</p></div>
              <strong>{result.knowledge_items_created}</strong>
            </li>
          </ul>
        </div>
      )}

      <form className="auth-form" onSubmit={handleSubmit}>
        <label>
          Project ID
          <input
            type="text"
            value={projectId}
            onChange={(e) => setProjectId(e.target.value)}
            placeholder="Enter project ID"
            required
          />
          <p className="muted">Reconstruction requires at least one ingested source for this project.</p>
        </label>

        <button type="submit" className="auth-button" disabled={loading || !projectId}>
          {loading ? "Reconstructing..." : "Run reconstruction"}
        </button>
      </form>

      <p className="muted" style={{ marginTop: 16 }}>
        <a href="/intelligence" className="link-btn">Back to intelligence</a>
      </p>
    </section>
  );
}
