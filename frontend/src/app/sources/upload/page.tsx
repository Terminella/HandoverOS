"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { apiPost } from "../../../lib/api";
import { getStoredToken } from "../../../lib/api";
import { Upload, FileText, FileCode } from "lucide-react";

const SUPPORTED_EXTENSIONS = [".pdf", ".docx", ".txt", ".csv"];

function iconForExtension(ext: string) {
  switch (ext) {
    case ".pdf": return FileText;
    case ".docx": return FileCode;
    case ".csv": return FileText;
    default: return FileText;
  }
}

interface UploadedFile {
  file: File;
  preview: string;
  status: "pending" | "uploading" | "success" | "error";
  progress: number;
  error?: string;
}

export default function SourceUploadPage() {
  const router = useRouter();
  const token = getStoredToken() ?? undefined;
  const [projectId, setProjectId] = useState("");
  useEffect(() => {
  const syncProject = () => {
    const selectedId = localStorage.getItem("handoveros-selected-project");
    setProjectId(selectedId || "");
  };

  const handleProjectChange = (event: Event) => {
    const customEvent = event as CustomEvent<{ projectId: string }>;
    setProjectId(customEvent.detail.projectId || "");
  };

  syncProject();

  window.addEventListener("handoveros-project-change", handleProjectChange);
  window.addEventListener("storage", syncProject);

  return () => {
    window.removeEventListener("handoveros-project-change", handleProjectChange);
    window.removeEventListener("storage", syncProject);
  };
}, []);
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [dragActive, setDragActive] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  useEffect(() => {
    const handleDragOver = (e: DragEvent) => {
      e.preventDefault();
      setDragActive(true);
    };
    const handleDragLeave = (e: DragEvent) => {
      e.preventDefault();
      setDragActive(false);
    };
    const handleDrop = (e: DragEvent) => {
      e.preventDefault();
      setDragActive(false);
      if (e.dataTransfer) {
        addFiles(Array.from(e.dataTransfer.files));
      }
    };

    window.addEventListener("dragover", handleDragOver);
    window.addEventListener("dragleave", handleDragLeave);
    window.addEventListener("drop", handleDrop);
    return () => {
      window.removeEventListener("dragover", handleDragOver);
      window.removeEventListener("dragleave", handleDragLeave);
      window.removeEventListener("drop", handleDrop);
    };
  }, []);

  const addFiles = useCallback((newFiles: FileList | File[]) => {
    const fileArray = Array.from(newFiles);
    const newUploads: UploadedFile[] = fileArray.map((f) => {
      const ext = f.name.toLowerCase().endsWith(".")
        ? ""
        : f.name.slice(f.name.lastIndexOf(".")).toLowerCase();
      const supported = SUPPORTED_EXTENSIONS.includes(ext);
      return {
        file: f,
        preview: URL.createObjectURL(f),
        status: supported ? "pending" : "error",
        progress: 0,
        error: supported ? undefined : `Unsupported format: ${ext || "unknown"}`,
      };
    });
    setFiles((prev) => [...prev, ...newUploads]);
  }, []);

  const removeFile = (index: number) => {
    setFiles((prev) => {
      URL.revokeObjectURL(prev[index].preview);
      return prev.filter((_, i) => i !== index);
    });
  };

  const retryFile = (index: number) => {
    setFiles((prev) => {
      const next = [...prev];
      next[index] = { ...next[index], status: "pending", progress: 0, error: undefined };
      return next;
    });
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) addFiles(e.target.files);
  };

  const uploadAll = async () => {
    if (!projectId) {
      setError("Please select or enter a project ID.");
      return;
    }
    const pending = files.filter((f) => f.status === "pending" || f.status === "error");
    if (pending.length === 0) {
      setError("No files to upload.");
      return;
    }

    setUploading(true);
    setError("");
    setSuccess("");

    for (let i = 0; i < pending.length; i++) {
      const fileIndex = files.findIndex((f) => f === pending[i]);
      const formData = new FormData();
      formData.append("file", pending[i].file);

        setFiles((prev) => {
          const next = [...prev];
          next[fileIndex] = { ...next[fileIndex], status: "uploading", progress: 0 };
          return next;
        });

      try {
        await apiPost<{ id: string; name: string; message: string }>(
          `/sources/upload?project_id=${encodeURIComponent(projectId)}`,
          formData,
          token
        );

        setFiles((prev) => {
          const next = [...prev];
          next[fileIndex] = { ...next[fileIndex], status: "success", progress: 100 };
          return next;
        });
        setSuccess(`${pending[i].file.name} uploaded successfully.`);
      } catch (err) {
        setFiles((prev) => {
          const next = [...prev];
          next[fileIndex] = {
            ...next[fileIndex],
            status: "error",
            error: err instanceof Error ? err.message : "Upload failed",
          };
          return next;
        });
      }
    }

    setUploading(false);
  };

  const supportedList = SUPPORTED_EXTENSIONS.join(", ").toUpperCase();

  return (
    <section className="card">
      <div className="card-head">
        <div>
          <h1 className="card-title">Upload Sources</h1>
          <p className="muted">Drag and drop files or click to browse. Supported: {supportedList}</p>
        </div>
      </div>

      {error && <p className="auth-error" role="alert">{error}</p>}
      {success && <p className="muted" role="status">{success}</p>}

      <div
        className={`drop-zone ${dragActive ? "drag-active" : ""}`}
        onDragOver={(e) => { e.preventDefault(); setDragActive(true); }}
        onDragLeave={(e) => { e.preventDefault(); setDragActive(false); }}
        onDrop={(e) => { e.preventDefault(); setDragActive(false); if (e.dataTransfer) addFiles(Array.from(e.dataTransfer.files)); }}
      >
        <input
          type="file"
          multiple
          onChange={handleFileInput}
          accept={SUPPORTED_EXTENSIONS.join(",")}
          style={{ display: "none" }}
        />
        <div className="drop-content">
          {dragActive ? (
            <>
              <Upload size={48} aria-hidden="true" />
              <p>Drop files here</p>
            </>
          ) : (
            <>
              <Upload size={48} aria-hidden="true" />
              <p>Drag and drop files here, or <span className="link-btn" onClick={() => (document.querySelector('input[type=file]') as HTMLInputElement | null)?.click()}>browse</span></p>
              <p className="muted">Select multiple files. PDF, DOCX, TXT, CSV</p>
            </>
          )}
        </div>
      </div>

      <label className="project-label">
        Project ID
        <input
          type="text"
          value={projectId}
          onChange={(e) => setProjectId(e.target.value)}
          placeholder="Enter project ID"
          required
        />
      </label>

      {files.length > 0 && (
        <ul className="rows">
          {files.map((f, index) => {
            const Icon = iconForExtension(f.file.name.slice(f.file.name.lastIndexOf(".")).toLowerCase());
            return (
              <li key={index} className="row-item">
                <div className="row-text">
                  <p className="row-title">{f.file.name}</p>
                  <p className="muted">
                    {f.file.type} &middot; {(f.file.size / 1024).toFixed(1)} KB
                  </p>
                </div>
                {f.status === "uploading" ? (
                  <div className="bar" style={{ width: 120, height: 6 }}>
                    <div className="bar-fill" style={{ width: `${f.progress}%` }} />
                  </div>
                ) : f.status === "success" ? (
                  <span className="chip chip-verified">Uploaded</span>
                ) : (
                  <>
                    <span className="chip chip-danger">Error</span>
                    {f.error && <span className="muted" style={{ marginLeft: 8 }}>{f.error}</span>}
                    <button
                      type="button"
                      className="link-btn"
                      onClick={() => retryFile(index)}
                      style={{ marginLeft: 8 }}
                    >
                      Retry
                    </button>
                    <button
                      type="button"
                      className="link-btn"
                      onClick={() => removeFile(index)}
                      style={{ marginLeft: 8 }}
                    >
                      Remove
                    </button>
                  </>
                )}
                {f.status === "error" && f.error && (
                  <p className="muted" style={{ marginTop: 4 }}>{f.error}</p>
                )}
              </li>
            );
          })}
        </ul>
      )}

      <div style={{ marginTop: 20, display: "flex", gap: 12 }}>
        <button
          type="button"
          className="action-btn"
          disabled={uploading || files.length === 0 || !projectId}
          onClick={uploadAll}
        >
          {uploading ? "Uploading..." : "Upload selected"}
        </button>
        <button
          type="button"
          className="link-btn"
          onClick={() => router.push("/sources")}
        >
          Back to sources
        </button>
      </div>
    </section>
  );
}
