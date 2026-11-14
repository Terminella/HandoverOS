"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { apiPost } from "../../../lib/api";
import { getStoredToken } from "../../../lib/api";

export default function CreateProjectPage() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const token = getStoredToken() ?? undefined;

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const result = await apiPost<{ message: string; project: { id: string; name: string } }>(
        "/projects",
        { name: name.trim(), description: description.trim() },
        token
      );

      if (result.project?.id) {
        router.push("/projects");
      } else {
        router.push("/projects");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create project.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="card">
      <div className="card-head">
        <div>
          <h1 className="card-title">Create Project</h1>
          <p className="muted">Start a new project workspace for knowledge handover.</p>
        </div>
      </div>

      {error && (
        <p className="auth-error" role="alert">{error}</p>
      )}

      <form className="auth-form" onSubmit={handleSubmit}>
        <label>
          Project name
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="e.g. Customer Migration Q4"
            required
            minLength={2}
            maxLength={180}
          />
        </label>

        <label>
          Description (optional)
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="What is this project about?"
            rows={3}
          />
        </label>

        <button type="submit" className="auth-button" disabled={loading}>
          {loading ? "Creating..." : "Create project"}
        </button>
      </form>

      <p className="muted" style={{ marginTop: 16 }}>
        Already have a project?{" "}
        <a href="/projects" className="link-btn">View all projects</a>
      </p>
    </section>
  );
}
