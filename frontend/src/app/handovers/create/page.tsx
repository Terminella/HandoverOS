"use client";

import { useEffect, useState } from "react";
import { apiPost, getStoredToken } from "../../../lib/api";

const PROJECT_STORAGE_KEY = "handoveros-selected-project";

export default function CreateHandoverPage() {
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

  useEffect(() => {
    const syncProject = () => {
      setProjectId(localStorage.getItem(PROJECT_STORAGE_KEY) || "");
    };

    const handleProjectChange = (event: Event) => {
      const { projectId: nextProjectId } = (
        event as CustomEvent<{ projectId?: string }>
      ).detail ?? {};
      setProjectId(nextProjectId || "");
    };

    syncProject();
    window.addEventListener("handoveros-project-change", handleProjectChange);
    window.addEventListener("storage", syncProject);

    return () => {
      window.removeEventListener("handoveros-project-change", handleProjectChange);
      window.removeEventListener("storage", syncProject);
    };
  }, []);

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
    <section className="card section-card section-handover-create">
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
        <p className="muted">
          {projectId
            ? `The selected Topbar project will be used (ID: ${projectId}).`
            : "Select a project in the Topbar to generate a handover."}
        </p>
        <p className="muted">Requires verified knowledge items. Run reconstruction first.</p>

        <button type="submit" className="auth-button" disabled={loading || !projectId.trim()}>
          {loading ? "Generating..." : "Generate handover"}
        </button>
      </form>

      <p className="muted" style={{ marginTop: 16 }}>
        <a href="/handovers" className="link-btn">Back to handovers</a>
      </p>
    </section>
  );
}
