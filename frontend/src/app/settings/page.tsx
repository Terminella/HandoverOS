"use client";

import { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";
import { useRouter } from "next/navigation";
import {
  AIConfigurationDraft,
  ExecutionMode,
  LlmStatus,
  ModelCapability,
  OllamaModel,
  ProviderType,
  discoverOllamaModels,
  getLlmStatus,
  getStoredToken,
  getSystemHealth,
  selectOllamaModel,
  testOllamaCompatibility,
  testOllamaConnection,
} from "../../lib/api";
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
type ModelState = "idle" | "draft" | "discovering" | "selected" | "testing" | "ready" | "unavailable" | "error";
type ConnectionState = "idle" | "checking" | "connected" | "unavailable" | "error";

type ProviderOption = {
  id: ProviderType;
  label: string;
  mode: ExecutionMode;
  description: string;
  backendSupported: boolean;
};

const PROVIDERS: ProviderOption[] = [
  { id: "ollama", label: "Ollama", mode: "local", description: "Run a local model through your Ollama server.", backendSupported: true },
  { id: "openai", label: "OpenAI", mode: "cloud", description: "Use OpenAI models with your own API key.", backendSupported: false },
  { id: "openrouter", label: "OpenRouter", mode: "cloud", description: "Use models from multiple providers through OpenRouter.", backendSupported: false },
  { id: "gemini", label: "Google Gemini", mode: "cloud", description: "Use Google Gemini models with your own API key.", backendSupported: false },
  { id: "xai", label: "xAI / Grok", mode: "cloud", description: "Use xAI Grok models with your own API key.", backendSupported: false },
  { id: "anthropic", label: "Anthropic", mode: "cloud", description: "Use Claude models with your own API key.", backendSupported: false },
  { id: "custom", label: "Custom OpenAI-compatible", mode: "cloud", description: "Connect a compatible private or self-hosted endpoint.", backendSupported: false },
];

const EMPTY_DRAFT: AIConfigurationDraft = {
  provider_type: "ollama",
  execution_mode: "local",
  base_url: "http://127.0.0.1:11434",
  model_id: "",
  credential: { kind: "unchanged" },
};

function statusLabel(status: ConnectionState): string {
  if (status === "checking") return "Testing";
  if (status === "connected") return "Connected";
  if (status === "unavailable") return "Unavailable";
  if (status === "error") return "Error";
  return "Not tested";
}

function modelStatusLabel(status: ModelState): string {
  if (status === "draft") return "Draft model";
  if (status === "discovering") return "Discovering";
  if (status === "selected") return "Validated";
  if (status === "testing") return "Testing";
  if (status === "ready") return "Compatible";
  if (status === "unavailable" || status === "error") return "Unavailable";
  return "Not tested";
}

export default function SettingsPage() {
  const router = useRouter();
  const token = getStoredToken() ?? undefined;
  const [activeTab, setActiveTab] = useState<TabId>("general");
  const [health, setHealth] = useState<{ backend: boolean; message: string } | null>(null);
  const [llmStatus, setLlmStatus] = useState<LlmStatus | null>(null);
  const [mode, setMode] = useState<ExecutionMode>("local");
  const [provider, setProvider] = useState<ProviderType>("ollama");
  const [draft, setDraft] = useState<AIConfigurationDraft>(EMPTY_DRAFT);
  const [models, setModels] = useState<OllamaModel[]>([]);
  const [connectionStatus, setConnectionStatus] = useState<ConnectionState>("idle");
  const [modelStatus, setModelStatus] = useState<ModelState>("idle");
  const [lastTestedModel, setLastTestedModel] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    async function loadStatus() {
      const [systemResult, llmResult] = await Promise.allSettled([getSystemHealth(token), getLlmStatus(token)]);
      if (!mounted) return;
      if (systemResult.status === "fulfilled") {
        setHealth({ backend: systemResult.value.status === "healthy", message: "Backend is reachable" });
      } else {
        const message = systemResult.reason instanceof Error ? systemResult.reason.message : "Backend is not reachable";
        setHealth({ backend: false, message });
        setError(message);
      }
      if (llmResult.status === "fulfilled") {
        const status = llmResult.value;
        setLlmStatus(status);
        setProvider(status.provider === "ollama" ? "ollama" : "custom");
        setMode(status.is_ollama_provider ? "local" : "cloud");
        setDraft((current) => ({
          ...current,
          provider_type: status.provider === "ollama" ? "ollama" : current.provider_type,
          execution_mode: status.is_ollama_provider ? "local" : current.execution_mode,
          base_url: status.ollama_base_url || current.base_url,
          model_id: status.ollama_model || current.model_id,
        }));
      } else if (systemResult.status === "fulfilled") {
        setError(llmResult.reason instanceof Error ? llmResult.reason.message : "AI configuration is unavailable.");
      }
    }
    loadStatus();
    return () => { mounted = false; };
  }, [token]);

  function updateDraft(changes: Partial<AIConfigurationDraft>) {
    setDraft((current) => ({ ...current, ...changes }));
    setModelStatus("draft");
    setLastTestedModel(null);
  }

  async function discoverModels() {
    setModelStatus("discovering");
    setConnectionStatus("checking");
    setError(null);
    try {
      const result = await discoverOllamaModels(token);
      setModels(result.models);
      setModelStatus(result.models.length > 0 ? "selected" : "unavailable");
      setConnectionStatus("connected");
      if (!draft.model_id && result.models.length > 0) updateDraft({ model_id: result.models[0].name });
    } catch (err) {
      setModels([]);
      setModelStatus("unavailable");
      setConnectionStatus("error");
      setError(err instanceof Error ? err.message : "Model discovery failed.");
    }
  }

  async function testConnection() {
    setConnectionStatus("checking");
    setError(null);
    try {
      const result = await testOllamaConnection(token);
      setConnectionStatus(result.status === "connected" ? "connected" : "unavailable");
      if (result.status !== "connected") {
        setError(result.message || "Ollama is unavailable.");
        return;
      }
      await discoverModels();
    } catch (err) {
      setConnectionStatus("error");
      setError(err instanceof Error ? err.message : "Connection test failed.");
    }
  }

  async function validateSelectedModel() {
    const model = draft.model_id.trim();
    if (!model) {
      setError("Enter or select a model before testing it.");
      setModelStatus("error");
      return;
    }
    setModelStatus("testing");
    setError(null);
    try {
      const result = await selectOllamaModel(model, token);
      setModelStatus("selected");
      setLastTestedModel(result.model || model);
    } catch (err) {
      setModelStatus("error");
      setError(err instanceof Error ? err.message : "Model validation failed.");
    }
  }

  async function testCompatibility() {
    if (!draft.model_id.trim()) {
      setError("Enter or select a model before testing compatibility.");
      setModelStatus("error");
      return;
    }
    setModelStatus("testing");
    setError(null);
    try {
      const result = await testOllamaCompatibility(token);
      setModelStatus(result.status === "compatible" ? "ready" : "error");
      setLastTestedModel(result.model || draft.model_id);
      if (result.status !== "compatible") setError(result.message || "The model did not pass compatibility testing.");
    } catch (err) {
      setModelStatus("error");
      setError(err instanceof Error ? err.message : "Compatibility testing failed.");
    }
  }

  function handleModeChange(nextMode: ExecutionMode) {
    setMode(nextMode);
    setError(null);
    if (nextMode === "local") {
      setProvider("ollama");
      updateDraft({ provider_type: "ollama", execution_mode: "local", base_url: draft.base_url || EMPTY_DRAFT.base_url });
    } else {
      setProvider("openai");
      updateDraft({ provider_type: "openai", execution_mode: "cloud", base_url: "" });
    }
  }

  function handleProviderChange(nextProvider: ProviderType) {
    const selected = PROVIDERS.find((item) => item.id === nextProvider) ?? PROVIDERS[0];
    setProvider(nextProvider);
    setMode(selected.mode);
    setError(null);
    updateDraft({ provider_type: selected.id, execution_mode: selected.mode, base_url: selected.mode === "local" ? draft.base_url || EMPTY_DRAFT.base_url : "" });
  }

  function handleLogout() {
    clearToken();
    router.replace("/login");
  }

  const selectedProvider = PROVIDERS.find((item) => item.id === provider) ?? PROVIDERS[0];
  const isOllama = selectedProvider.id === "ollama";
  const capabilityList: ModelCapability[] = ["chat", "structured_output"];

  return (
    <section className="card section-card section-settings">
      <div className="card-head"><div><h1 className="card-title">Settings</h1><p className="muted">Configure application preferences and workspace options.</p></div></div>
      <div className="settings-tabs">
        {TABS.map((tab) => <button key={tab.id} type="button" className={`tab-btn ${activeTab === tab.id ? "tab-active" : ""}`} onClick={() => setActiveTab(tab.id)}>{tab.label}</button>)}
      </div>

      {activeTab === "general" && <div className="settings-panel"><h2>Appearance</h2><p className="muted">Choose your preferred colour theme.</p><p className="muted">Use the theme toggle in the sidebar to switch between light and dark mode.</p></div>}

      {activeTab === "ai" && (
        <div className="settings-panel">
          <h2>AI &amp; Intelligence</h2>
          <p className="muted">Choose a local model or prepare a cloud/BYOK configuration. Cloud saving and credentials are awaiting backend integration.</p>

          <div style={{ display: "flex", gap: 10, flexWrap: "wrap", margin: "18px 0" }}>
            {(["local", "cloud"] as ExecutionMode[]).map((option) => <button key={option} type="button" className={`action-btn ${mode === option ? "chip-verified" : ""}`} onClick={() => handleModeChange(option)}>{option === "local" ? "Local LLM" : "Cloud / BYOK"}</button>)}
          </div>

          <section style={{ marginBottom: 20 }}>
            <h3>Provider</h3>
            <label>Provider type<select value={provider} onChange={(event) => handleProviderChange(event.target.value as ProviderType)}>{PROVIDERS.filter((item) => item.mode === mode).map((item) => <option key={item.id} value={item.id}>{item.label}</option>)}</select></label>
            <p className="muted" style={{ marginTop: 8 }}>{selectedProvider.description}</p>
          </section>

          <section style={{ marginBottom: 20 }}>
            <h3>Configurations</h3>
            <div className="rows">
              <div className="row-item"><div className="row-text"><p className="row-title">Current configuration</p><span className="muted">Environment default</span></div><span className={`chip ${llmStatus ? "chip-verified" : "chip-pending"}`}>{llmStatus ? "Active" : "Unknown"}</span></div>
              <div className="row-item"><div className="row-text"><p className="row-title">Configuration scope</p></div><strong>Environment</strong></div>
              <div className="row-item"><div className="row-text"><p className="row-title">Credential state</p></div><strong>Not managed by current backend</strong></div>
            </div>
            <p className="muted" style={{ marginTop: 8 }}>The current backend exposes one environment configuration. Multiple saved configuration IDs will appear here after backend support is available.</p>
          </section>

          {isOllama ? (
            <section>
              <h3>Local Ollama configuration</h3>
              <label>Server URL<input value={draft.base_url} onChange={(event) => updateDraft({ base_url: event.target.value })} placeholder="http://127.0.0.1:11434" /></label>
              <label>Installed model<select value={models.some((model) => model.name === draft.model_id) ? draft.model_id : ""} onChange={(event) => updateDraft({ model_id: event.target.value })}><option value="">Choose discovered model</option>{models.map((model) => <option key={model.name} value={model.name}>{model.name}</option>)}</select></label>
              <label>Or enter a model ID<input value={draft.model_id} onChange={(event) => updateDraft({ model_id: event.target.value })} placeholder="Any model installed on this server" /></label>
              <div style={{ display: "flex", gap: 10, flexWrap: "wrap", marginTop: 12 }}>
                <button type="button" className="action-btn" disabled={connectionStatus === "checking"} onClick={discoverModels}>{connectionStatus === "checking" ? <><Loader2 size={16} /> Discovering...</> : "Discover models"}</button>
                <button type="button" className="action-btn" disabled={connectionStatus === "checking"} onClick={testConnection}>{connectionStatus === "checking" ? "Testing..." : "Test connection"}</button>
                <button type="button" className="action-btn" disabled={!draft.model_id.trim() || modelStatus === "testing"} onClick={validateSelectedModel}>Validate model</button>
                <button type="button" className="action-btn" disabled={!draft.model_id.trim() || modelStatus === "testing"} onClick={testCompatibility}>Test compatibility</button>
              </div>
              <div className="rows" style={{ marginTop: 14 }}>
                <div className="row-item"><div className="row-text"><p className="row-title">Connection</p></div><span className={`chip ${connectionStatus === "connected" ? "chip-verified" : connectionStatus === "error" || connectionStatus === "unavailable" ? "chip-danger" : "chip-pending"}`}>{statusLabel(connectionStatus)}</span></div>
                <div className="row-item"><div className="row-text"><p className="row-title">Model state</p></div><span className={`chip ${modelStatus === "ready" ? "chip-verified" : modelStatus === "error" || modelStatus === "unavailable" ? "chip-danger" : "chip-pending"}`}>{modelStatusLabel(modelStatus)}</span></div>
                <div className="row-item"><div className="row-text"><p className="row-title">Capabilities</p></div><strong>{capabilityList.join(" · ")}</strong></div>
              </div>
              {lastTestedModel && <p className="muted" style={{ marginTop: 8 }}>Last backend-confirmed model: {lastTestedModel}</p>}
              {llmStatus && <p className="muted" style={{ marginTop: 8 }}>Backend model: {llmStatus.ollama_model || "automatic discovery"}. Selection mode: {llmStatus.model_selection_mode}.</p>}
            </section>
          ) : (
            <section className="auth-error" role="status">
              <strong>{selectedProvider.label} is not available yet.</strong>
              <p style={{ margin: "6px 0 0" }}>The current backend has no provider configuration, credential, discovery, or test endpoint for this provider. No credential has been requested or transmitted.</p>
              <label style={{ marginTop: 12 }}>Endpoint/base URL (draft only)<input value={draft.base_url} onChange={(event) => updateDraft({ base_url: event.target.value })} placeholder={selectedProvider.id === "custom" ? "https://your-endpoint.example/v1" : "Provider default endpoint"} /></label>
              <p className="muted" style={{ margin: "8px 0 0" }}>This draft value is not sent or saved until backend integration is approved.</p>
            </section>
          )}

          {error && <p className="auth-error" role="alert" style={{ marginTop: 16 }}>{error}</p>}
          <p className="muted" style={{ marginTop: 16, fontSize: "0.85rem" }}>Credentials are not stored or managed by this frontend. Omitted credentials are never treated as deletion.</p>
        </div>
      )}

      {activeTab === "processing" && <div className="settings-panel"><h2>Processing</h2><ul className="rows"><li className="row-item"><div className="row-text"><p className="row-title">Supported file formats</p></div><strong>PDF, DOCX, TXT, CSV</strong></li><li className="row-item"><div className="row-text"><p className="row-title">Max input characters per source</p></div><strong>100,000</strong></li><li className="row-item"><div className="row-text"><p className="row-title">Max sources per batch</p></div><strong>25</strong></li><li className="row-item"><div className="row-text"><p className="row-title">Max claims per source</p></div><strong>30</strong></li></ul><p className="muted" style={{ marginTop: 16, fontSize: "0.85rem" }}>Processing limits are configured via environment variables and require a backend restart to change.</p></div>}
      {activeTab === "workspace" && <div className="settings-panel"><h2>Workspace</h2><p className="muted">Select your active project from the project switcher in the top navigation.</p><p className="muted">Project selection is remembered across sessions using local storage.</p></div>}
      {activeTab === "account" && <div className="settings-panel"><h2>Account &amp; Security</h2><p className="muted">Your session is managed by the backend. Sessions expire after 12 hours.</p><div style={{ marginTop: 20 }}><button type="button" className="action-btn" style={{ background: "var(--danger)", color: "var(--on-primary)" }} onClick={handleLogout}>Sign out</button></div></div>}
      {activeTab === "system" && <div className="settings-panel"><h2>System Health</h2>{health && <ul className="rows"><li className="row-item"><div className="row-text"><p className="row-title">Backend</p></div><span className={`chip ${health.backend ? "chip-verified" : "chip-danger"}`}>{health.backend ? "Healthy" : "Unreachable"}</span></li><li className="row-item"><div className="row-text"><p className="row-title">Message</p></div><strong>{health.message}</strong></li></ul>}<div style={{ marginTop: 20 }}><button type="button" className="action-btn" disabled={loading} onClick={async () => { setLoading(true); try { const result = await getSystemHealth(token); setHealth({ backend: result.status === "healthy", message: result.status === "healthy" ? "Backend is reachable" : result.status }); } catch (err) { setHealth({ backend: false, message: err instanceof Error ? err.message : "Backend is not reachable" }); } finally { setLoading(false); } }}>{loading ? "Refreshing..." : "Refresh health"}</button></div></div>}
    </section>
  );
}
