"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { apiPost, getStoredToken } from "../../../lib/api";

export default function CreateHandoverPage() {
  const router = useRouter();
  const [projectId, setProjectId] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<{
    id: string;
    projectId: string;
    version: string;
    status: string;
    generatedAt: string;
    preparedBy: string;
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
        id: string;
        projectId: string;
        version: string;
        status: string;
        generatedAt: string;
        preparedBy: string;
        message: string;
      }>("/handovers", { project_id: projectId }, token);

      setResult(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Handover generation failed.");
    } finally {
      setLoading(false);
    }
  }

  async function handleApprove() {
    if (!result) return;
    setLoading(true);
    try {
      await apiPost<{ status: string; message: string }>(
        `/handovers/${result.id}/approve`,
        {},
        token
      );
      setResult({ ...result, status: "approved" });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Approval failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="card">
      <div className="card-head">
        <div>
          <h1 className="card-title">Generate Handover</h1>
          <p className="muted">Create a structured handover from verified knowledge items.</p>
        </div>
      </div>

      {error && <p className="auth-error" role="alert">{error}</p>}
      {result && (
        <div style={{ background: "var(--primary-soft)", border: "1px solid var(--border)", borderRadius: "8px", padding: 16, marginBottom: 20 }}>
          <h2 style={{ margin: 0, fontSize: "1rem", color: "var(--primary)" }}>Handover {result.version} created</h2>
          <ul className="rows">
            <li className="row-item">
              <div className="row-text"><p className="row-title">Status</p></div>
              <strong>{result.status}</strong>
            </li>
            <li className="row-item">
              <div className="row-text"><p className="row-title">Generated</p></div>
              <strong>{result.generatedAt}</strong>
            </li>
            <li className="row-item">
              <div className="row-text"><p className="row-title">Prepared by</p></div>
              <strong>{result.preparedBy}</strong>
            </li>
          </ul>
          {result.status === "draft" && (
            <button
              type="button"
              className="action-btn"
              disabled={loading}
              onClick={handleApprove}
            >
              {loading ? "Approving..." : "Approve handover"}
            </button>
          )}
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
          <p className="muted">Requires verified knowledge items. Run reconstruction first.</p>
        </label>

        <button type="submit" className="auth-button" disabled={loading || !projectId}>
          {loading ? "Generating..." : "Generate handover"}
        </button>
      </form>

      <p className="muted" style={{ marginTop: 16 }}>
        <a href="/handovers" className="link-btn">Back to handovers</a>
      </p>
    </section>
  );
}
