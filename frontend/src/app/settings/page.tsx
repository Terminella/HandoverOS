"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { useRouter } from "next/navigation";
import { RefreshCw, ChevronRight, Loader2 } from "lucide-react";
import { apiRequest, apiPost, getStoredToken } from "../../lib/api";
import { clearToken } from "../../lib/auth";

const TABS = [
  { id: "general", label: "General" },
  { id: "ai", label: "AI & Intelligence" },
  { id: "processing", label: "Processing" },
  { id: "workspace", label: "Workspace" },
  { id: "account", label: "Account & Security" },
  { id: "system", label: "System Health" },
] as const;

type TabId = (typeof TABS)[number]["id"];

type OllamaModel = {
  name: string;
  size: number | null;
  digest: string | null;
  modified_at: string | null;
  parameter_size: string | null;
  quantization: string | null;
  family: string | null;
};

type LlmStatus = {
  provider: string;
  model: string | null;
  ollama_base_url: string;
  ollama_model: string | null;
  model_selection_mode: string;
  is_ollama_provider: boolean;
};

type ConnectionStatus = "idle" | "checking" | "connected" | "disconnected" | "error";
type ModelStatus = "idle" | "discovering" | "discovered" | "testing" | "ready" | "incompatible" | "unavailable";

export default function SettingsPage() {
  const router = useRouter();
  const token = getStoredToken() ?? undefined;
  const mountedRef = useRef(true);
  const [activeTab, setActiveTab] = useState<TabId>("general");
  const [health, setHealth] = useState<{ backend: boolean; message: string } | null>(null);
  const [llmStatus, setLlmStatus] = useState<LlmStatus | null>(null);
  const [models, setModels] = useState<OllamaModel[]>([]);
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>("idle");
  const [modelStatus, setModelStatus] = useState<ModelStatus>("idle");
  const [selectedModel, setSelectedModel] = useState<string>("");
  const [selectionMode, setSelectionMode] = useState<"auto" | "manual">("auto");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    mountedRef.current = true;
    async function fetchStatus() {
      try {
        const [sys, llm] = await Promise.all([
          apiRequest<{ status: string }>("/system/health", token),
          apiRequest<LlmStatus>("/system/llm/status", token),
        ]);
        if (mountedRef.current) {
          setHealth({ backend: sys.status === "healthy", message: "Backend is reachable" });
          setLlmStatus(llm);
          setSelectionMode(llm.model_selection_mode === "manual" ? "manual" : "auto");
          setSelectedModel(llm.ollama_model || "");
        }
      } catch {
        if (mountedRef.current) {
          setHealth({ backend: false, message: "Backend is not reachable" });
        }
      }
    }
    fetchStatus();
    return () => { mountedRef.current = false; };
  }, [token]);

  const fetchModels = useCallback(async () => {
    setModelStatus("discovering");
    setError(null);
    try {
      const res = await apiRequest<{ models: OllamaModel[]; count: number }>("/system/llm/models", token);
      if (mountedRef.current) {
        setModels(res.models);
        setModelStatus(res.models.length > 0 ? "discovered" : "unavailable");
        if (!selectedModel && res.models.length > 0) {
          setSelectedModel(res.models[0].name);
        }
      }
    } catch (err) {
      if (mountedRef.current) {
        setModelStatus("unavailable");
        setError(err instanceof Error ? err.message : "Failed to discover models.");
      }
    } finally {
      if (mountedRef.current) {
        // keep connection status as-is
      }
    }
  }, [token, selectedModel]);

  const testConnection = useCallback(async () => {
    setConnectionStatus("checking");
    setError(null);
    try {
      const res = await apiPost<{ status: string; message: string; count: number }>("/system/llm/test", {}, token);
      if (mountedRef.current) {
        setConnectionStatus(res.status === "connected" ? "connected" : "disconnected");
        if (res.status === "connected" && res.count > 0) {
          await fetchModels();
        }
      }
    } catch (err) {
      if (mountedRef.current) {
        setConnectionStatus("error");
        setError(err instanceof Error ? err.message : "Connection test failed.");
      }
    }
  }, [token, fetchModels]);

  const testCompatibility = useCallback(async () => {
    const modelToTest = selectedModel || (llmStatus?.ollama_model || "");
    if (!modelToTest) {
      setError("No model selected to test.");
      return;
    }
    setModelStatus("testing");
    setError(null);
    try {
      const res = await apiPost<{ model: string; status: string; message: string; claims_extracted: number }>("/system/llm/compatibility-test", {}, token);
      if (mountedRef.current) {
        setModelStatus(res.status === "compatible" ? "ready" : "incompatible");
        if (res.status !== "compatible") {
          setError(`Compatibility test failed: ${res.message}`);
        }
      }
    } catch (err) {
      if (mountedRef.current) {
        setModelStatus("incompatible");
        setError(err instanceof Error ? err.message : "Compatibility test failed.");
      }
    }
  }, [token, selectedModel, llmStatus?.ollama_model]);

  const selectModel = useCallback(async (modelName: string) => {
    setModelStatus("testing");
    setError(null);
    try {
      await apiPost<{ status: string; message: string }>("/system/llm/select", { model: modelName }, token);
      if (mountedRef.current) {
        setSelectedModel(modelName);
        setSelectionMode("manual");
        await testCompatibility();
      }
    } catch (err) {
      if (mountedRef.current) {
        setModelStatus("unavailable");
        setError(err instanceof Error ? err.message : "Model selection failed.");
      }
    }
  }, [token, testCompatibility]);

  const useAutomaticSelection = useCallback(async () => {
    setModelStatus("discovering");
    setError(null);
    try {
      await fetchModels();
      if (mountedRef.current && models.length > 0) {
        setSelectedModel(models[0].name);
        setSelectionMode("auto");
        await testCompatibility();
      }
    } catch (err) {
      if (mountedRef.current) {
        setError(err instanceof Error ? err.message : "Automatic selection failed.");
      }
    }
  }, [token, fetchModels, testCompatibility, models.length]);

  function handleLogout() {
    clearToken();
    router.replace("/login");
  }

  return (
    <section className="card">
      <div className="card-head">
        <div>
          <h1 className="card-title">Settings</h1>
          <p className="muted">Configure application preferences and workspace options.</p>
        </div>
      </div>

      <div className="settings-tabs">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            type="button"
            className={`tab-btn ${activeTab === tab.id ? "tab-active" : ""}`}
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === "general" && (
        <div className="settings-panel">
          <h2>Appearance</h2>
          <p className="muted">Choose your preferred colour theme.</p>
          <p className="muted">Use the theme toggle in the sidebar to switch between light and dark mode.</p>
        </div>
      )}

      {activeTab === "ai" && (
        <div className="settings-panel">
          <h2>AI &amp; Intelligence</h2>

          <div style={{ marginBottom: 16 }}>
            <h3 style={{ margin: "0 0 8px 0", fontSize: "1rem", fontWeight: 600 }}>LLM Provider</h3>
            <ul className="rows">
              <li className="row-item">
                <div className="row-text"><p className="row-title">Provider</p></div>
                <strong>{llmStatus?.provider || "—"}</strong>
              </li>
              <li className="row-item">
                <div className="row-text"><p className="row-title">Base URL</p></div>
                <strong>{llmStatus?.ollama_base_url || "—"}</strong>
              </li>
              <li className="row-item">
                <div className="row-text"><p className="row-title">Selection mode</p></div>
                <strong>{selectionMode === "auto" ? "Automatic" : "Manual"}</strong>
              </li>
              <li className="row-item">
                <div className="row-text"><p className="row-title">Configured model</p></div>
                <strong>{llmStatus?.ollama_model || "<auto-discovery>"}</strong>
              </li>
            </ul>
          </div>

          <div style={{ marginBottom: 16 }}>
            <h3 style={{ margin: "0 0 8px 0", fontSize: "1rem", fontWeight: 600 }}>Connection</h3>
            <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 8 }}>
              <button
                type="button"
                className="action-btn"
                disabled={connectionStatus === "checking"}
                onClick={testConnection}
              >
                {connectionStatus === "checking" ? (
                  <span style={{ display: "flex", alignItems: "center", gap: 6 }}>
                    <Loader2 size={16} /> Testing…
                  </span>
                ) : (
                  <span>
                    <RefreshCw size={16} /> Test Connection
                  </span>
                )}
              </button>
              <span className={`chip ${connectionStatus === "connected" ? "chip-verified" : connectionStatus === "error" ? "chip-danger" : "chip-pending"}`}>
                {connectionStatus === "connected" ? "Connected" : connectionStatus === "disconnected" ? "Disconnected" : connectionStatus === "error" ? "Error" : "Not tested"}
              </span>
            </div>
            {connectionStatus === "connected" && (
              <p className="muted" style={{ marginTop: 4 }}>{`${models.length} model(s) installed`}</p>
            )}
            {error && <p className="auth-error" style={{ marginTop: 8 }}>{error}</p>}
          </div>

          <div style={{ marginBottom: 16 }}>
            <h3 style={{ margin: "0 0 8px 0", fontSize: "1rem", fontWeight: 600 }}>Model Discovery</h3>
            {modelStatus === "discovering" && (
              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <Loader2 size={16} /> Discovering models…
              </div>
            )}
            {models.length > 0 && (
              <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                <p className="muted" style={{ margin: 0 }}>{models.length} locally installed model(s)</p>
                <div style={{ display: "flex", flexDirection: "column", gap: 6, maxHeight: 200, overflowY: "auto", border: "1px solid var(--border)", borderRadius: 8, padding: 10, background: "var(--surface-2)" }}>
                  {models.map((m) => {
                    const isSelected = m.name === selectedModel;
                    return (
                      <div key={m.name} style={{ display: "flex", alignItems: "center", gap: 10, padding: 8, borderBottom: "1px solid var(--border)" }}>
                        <div style={{ flex: 1 }}>
                          <div style={{ fontWeight: 600 }}>{m.name}</div>
                          <div style={{ fontSize: "0.75rem", color: "var(--muted)" }}>
                            {m.parameter_size ? ` ${m.parameter_size}` : ""}{m.quantization ? ` · ${m.quantization}` : ""}{m.family ? ` · ${m.family}` : ""}
                          </div>
                        </div>
                        <button
                          type="button"
                          className={`action-btn ${isSelected ? "chip-verified" : ""}`}
                          disabled={isSelected || modelStatus === "discovering" || modelStatus === "testing"}
                          onClick={() => selectModel(m.name)}
                          style={{ padding: "4px 10px", fontSize: "0.8rem" }}
                        >
                          {isSelected ? "Selected" : "Select"}
                        </button>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
            {models.length === 0 && modelStatus !== "discovering" && (
              <p className="muted" style={{ margin: 0 }}>No models discovered. Test connection first.</p>
            )}
          </div>

          <div style={{ marginBottom: 16 }}>
            <h3 style={{ margin: "0 0 8px 0", fontSize: "1rem", fontWeight: 600 }}>Model Selection</h3>
            <div style={{ display: "flex", gap: 12, marginBottom: 12 }}>
              <button
                type="button"
                className={`action-btn ${selectionMode === "auto" ? "chip-verified" : ""}`}
                onClick={useAutomaticSelection}
                disabled={modelStatus === "discovering" || modelStatus === "testing"}
              >
                <span style={{ display: "flex", alignItems: "center", gap: 6 }}>
                  <ChevronRight size={14} /> Automatic selection
                </span>
              </button>
              <button
                type="button"
                className={`action-btn ${selectionMode === "manual" ? "chip-verified" : ""}`}
                onClick={() => setSelectionMode("manual")}
                disabled={models.length === 0}
              >
                Manual selection
              </button>
            </div>
            <div style={{ display: "flex", gap: 12 }}>
              <button
                type="button"
                className="action-btn"
                disabled={!selectedModel || modelStatus === "testing" || modelStatus === "discovering"}
                onClick={testCompatibility}
              >
                {modelStatus === "testing" ? (
                  <span style={{ display: "flex", alignItems: "center", gap: 6 }}>
                    <Loader2 size={16} /> Testing…
                  </span>
                ) : (
                  <span>
                    <RefreshCw size={16} /> Test Compatibility
                  </span>
                )}
              </button>
            </div>
            <div style={{ marginTop: 8 }}>
              <span className={`chip ${modelStatus === "ready" ? "chip-verified" : modelStatus === "incompatible" ? "chip-danger" : modelStatus === "unavailable" ? "chip-danger" : "chip-pending"}`}>
                {modelStatus === "ready" ? "Model ready" : modelStatus === "incompatible" ? "Incompatible" : modelStatus === "unavailable" ? "No models" : modelStatus === "testing" ? "Testing…" : "Not tested"}
              </span>
            </div>
            {error && <p className="auth-error" style={{ marginTop: 8 }}>{error}</p>}
          </div>

          <p className="muted" style={{ marginTop: 16, fontSize: "0.85rem" }}>
            Mock mode is only enabled when LLM_PROVIDER=mock is set explicitly. Ollama failures are reported as errors, not silently replaced.
          </p>
        </div>
      )}

      {activeTab === "processing" && (
        <div className="settings-panel">
          <h2>Processing</h2>
          <ul className="rows">
            <li className="row-item">
              <div className="row-text"><p className="row-title">Supported file formats</p></div>
              <strong>PDF, DOCX, TXT, CSV</strong>
            </li>
            <li className="row-item">
              <div className="row-text"><p className="row-title">Max input characters per source</p></div>
              <strong>100,000</strong>
            </li>
            <li className="row-item">
              <div className="row-text"><p className="row-title">Max sources per batch</p></div>
              <strong>25</strong>
            </li>
            <li className="row-item">
              <div className="row-text"><p className="row-title">Max claims per source</p></div>
              <strong>30</strong>
            </li>
          </ul>
          <p className="muted" style={{ marginTop: 16, fontSize: "0.85rem" }}>
            Processing limits are configured via environment variables and require a backend restart to change.
          </p>
        </div>
      )}

      {activeTab === "workspace" && (
        <div className="settings-panel">
          <h2>Workspace</h2>
          <p className="muted">Select your active project from the project switcher in the top navigation.</p>
          <p className="muted">Project selection is remembered across sessions using local storage.</p>
        </div>
      )}

      {activeTab === "account" && (
        <div className="settings-panel">
          <h2>Account &amp; Security</h2>
          <p className="muted">Your session is managed by the backend. Sessions expire after 12 hours.</p>
          <div style={{ marginTop: 20 }}>
            <button
              type="button"
              className="action-btn"
              style={{ background: "var(--danger)", color: "var(--on-primary)" }}
              onClick={handleLogout}
            >
              Sign out
            </button>
          </div>
        </div>
      )}

      {activeTab === "system" && (
        <div className="settings-panel">
          <h2>System Health</h2>
          {health && (
            <ul className="rows">
              <li className="row-item">
                <div className="row-text"><p className="row-title">Backend</p></div>
                <span className={`chip ${health.backend ? "chip-verified" : "chip-danger"}`}>
                  {health.backend ? "Healthy" : "Unreachable"}
                </span>
              </li>
              <li className="row-item">
                <div className="row-text"><p className="row-title">Message</p></div>
                <strong>{health.message}</strong>
              </li>
            </ul>
          )}
          <div style={{ marginTop: 20 }}>
            <button
              type="button"
              className="action-btn"
              onClick={() => {
                setLoading(true);
                fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api"}/system/health`, {
                  headers: { Authorization: `Bearer ${token}` },
                })
                  .then(async (r) => {
                    const data = await r.json();
                    setHealth({ backend: r.ok, message: data.status || "Unknown" });
                    setLoading(false);
                  })
                  .catch(() => {
                    setHealth({ backend: false, message: "Backend is not reachable" });
                    setLoading(false);
                  });
              }}
            >
              Refresh health
            </button>
          </div>
        </div>
      )}
    </section>
  );
}
