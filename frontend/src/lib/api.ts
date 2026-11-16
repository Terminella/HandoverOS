
import type {
  FindingReviewAction,
  IntelligenceChatResponse,
  IntelligenceFinding,
  IntelligenceRun,
} from "./types";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api";

export type ExecutionMode = "local" | "cloud";

export type ProviderType =
  | "ollama"
  | "openai"
  | "openrouter"
  | "gemini"
  | "xai"
  | "anthropic"
  | "custom";

export type ConfigurationScope = "environment" | "user" | "project" | "unknown";
export type CredentialState = "not_configured" | "configured" | "replacement_pending";
export type ConnectionState = "not_tested" | "testing" | "connected" | "unavailable" | "error";

export type CredentialOperation =
  | { kind: "unchanged" }
  | { kind: "replace"; value: string }
  | { kind: "remove" };

export type ModelCapability =
  | "chat"
  | "structured_output"
  | "vision"
  | "tools"
  | "thinking"
  | (string & {});

export type ModelDescriptor = {
  id: string;
  display_name?: string;
  capabilities?: ModelCapability[];
  size?: number | null;
  family?: string | null;
  parameter_size?: string | null;
  quantization?: string | null;
};

export type AIConfigurationSummary = {
  configuration_id: string;
  provider_type: ProviderType;
  execution_mode: ExecutionMode;
  display_name: string;
  base_url: string | null;
  model_id: string | null;
  capabilities: ModelCapability[];
  active: boolean;
  connection_status: ConnectionState;
  credential_state: CredentialState;
  scope?: ConfigurationScope;
};

export type AIConfigurationDraft = {
  configuration_id?: string;
  provider_type: ProviderType;
  execution_mode: ExecutionMode;
  base_url: string;
  model_id: string;
  credential: CredentialOperation;
};

export type OllamaModel = {
  name: string;
  size: number | null;
  digest: string | null;
  modified_at: string | null;
  parameter_size: string | null;
  quantization: string | null;
  family: string | null;
};

export type LlmStatus = {
  provider: string;
  model: string | null;
  ollama_base_url: string;
  ollama_model: string | null;
  model_selection_mode: string;
  is_ollama_provider: boolean;
};

function getStoredToken(): string | null {
  if (typeof window === "undefined") return null;
  try {
    return localStorage.getItem("handoveros-token");
  } catch {
    return null;
  }
}

function extractErrorMessage(error: unknown): string {
  if (error === null || error === undefined) {
    return "Request failed.";
  }

  if (typeof error === "string") {
    return error;
  }

  if (error instanceof Error) {
    return error.message;
  }

  if (typeof error === "object") {
    const detail = (error as { detail?: unknown }).detail;

    if (typeof detail === "string") {
      return detail;
    }

    if (Array.isArray(detail)) {
      // FastAPI validation errors return detail as an array of error objects.
      const messages = detail
        .filter((item): item is { msg?: string } =>
          item !== null && typeof item === "object" && "msg" in item
        )
        .map((item) => item.msg)
        .filter(Boolean);

      if (messages.length > 0) {
        return messages.join(". ");
      }

      return "Invalid request. Please check your input.";
    }

    if (typeof detail === "object" && detail !== null) {
      return JSON.stringify(detail);
    }

    return "Request failed.";
  }

  return "Request failed.";
}

async function apiCall<T>(
  endpoint: string,
  method: string,
  data?: unknown,
  token?: string
): Promise<T> {
  const effectiveToken = token ?? getStoredToken();

  const headers: Record<string, string> = {};
  if (effectiveToken) {
    headers["Authorization"] = `Bearer ${effectiveToken}`;
  }
  if (data !== undefined && !(data instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }

  const init: RequestInit = {
    method,
    headers,
    cache: "no-store",
  };
  if (data !== undefined) {
    init.body = data instanceof FormData ? data : JSON.stringify(data);
  }

  let response: Response;

  try {
    response = await fetch(`${API_BASE_URL}${endpoint}`, init);
  } catch (err) {
    // Network failure — backend unreachable.
    throw new Error("Unable to connect to the server.");
  }

  if (response.status === 401) {
    if (typeof window !== "undefined") {
      localStorage.removeItem("handoveros-token");
      window.location.replace("/login");
    }
    throw new Error("Authentication required. Please sign in again.");
  }

  if (!response.ok) {
    let errorBody: unknown = null;

    try {
      errorBody = await response.json();
    } catch {
      // Non-JSON error body — use status text as fallback.
      errorBody = null;
    }

    const message = extractErrorMessage(errorBody);

    if (response.status >= 500) {
      // Reconstruction and LLM endpoints return deliberately sanitised,
      // actionable details. Keep those details visible instead of replacing
      // every provider failure with the same generic message.
      if (typeof console !== "undefined") {
        console.error(`Server error ${response.status} for ${endpoint}`);
      }
      const exposesSafeDetail =
        endpoint.startsWith("/knowledge/") ||
        endpoint.startsWith("/system/llm/") ||
        endpoint.startsWith("/intelligence/");
      throw new Error(
        exposesSafeDetail && message !== "Request failed."
          ? message
          : "Something went wrong on the server. Please try again later."
      );
    }

    throw new Error(message);
  }

  return response.json() as Promise<T>;
}

export function apiRequest<T>(endpoint: string, token?: string): Promise<T> {
  return apiCall<T>(endpoint, "GET", undefined, token);
}

export function apiPost<T>(
  endpoint: string,
  data: unknown,
  token?: string
): Promise<T> {
  return apiCall<T>(endpoint, "POST", data, token);
}

export function apiPut<T>(
  endpoint: string,
  data: unknown,
  token: string
): Promise<T> {
  return apiCall<T>(endpoint, "PUT", data, token);
}

export function apiDelete<T>(
  endpoint: string,
  token?: string
): Promise<T> {
  return apiCall<T>(endpoint, "DELETE", undefined, token);
}

export function getSystemHealth(token?: string): Promise<{ status: string }> {
  return apiRequest<{ status: string }>("/system/health", token);
}

export function getLlmStatus(token?: string): Promise<LlmStatus> {
  return apiRequest<LlmStatus>("/system/llm/status", token);
}

export function createIntelligenceRun(
  projectId: string,
  sourceIds: string[],
  idempotencyKey: string,
  token?: string,
): Promise<IntelligenceRun> {
  return apiPost<IntelligenceRun>(
    `/intelligence/projects/${encodeURIComponent(projectId)}/runs`,
    { source_ids: sourceIds, idempotency_key: idempotencyKey },
    token,
  );
}

export function getIntelligenceRun(runId: string, token?: string): Promise<IntelligenceRun> {
  return apiRequest<IntelligenceRun>(`/intelligence/runs/${encodeURIComponent(runId)}`, token);
}

export function getIntelligenceFindings(
  projectId: string,
  token?: string,
): Promise<IntelligenceFinding[]> {
  return apiRequest<IntelligenceFinding[]>(
    `/intelligence/projects/${encodeURIComponent(projectId)}/findings`,
    token,
  );
}

export function getIntelligenceFinding(
  findingId: string,
  token?: string,
): Promise<IntelligenceFinding> {
  return apiRequest<IntelligenceFinding>(
    `/intelligence/findings/${encodeURIComponent(findingId)}`,
    token,
  );
}

export function reviewIntelligenceFinding(
  findingId: string,
  payload: {
    action: FindingReviewAction;
    reviewer_note?: string | null;
    corrected_content?: string | null;
    expected_version: number;
  },
  token?: string,
): Promise<IntelligenceFinding> {
  return apiPost<IntelligenceFinding>(
    `/intelligence/findings/${encodeURIComponent(findingId)}/review`,
    payload,
    token,
  );
}

export function sendIntelligenceChat(
  projectId: string,
  payload: {
    message: string;
    conversation_id?: string | null;
    source_ids?: string[] | null;
    run_id?: string | null;
  },
  token?: string,
): Promise<IntelligenceChatResponse> {
  return apiPost<IntelligenceChatResponse>(
    `/intelligence/projects/${encodeURIComponent(projectId)}/chat`,
    payload,
    token,
  );
}

export function discoverOllamaModels(token?: string): Promise<{ models: OllamaModel[]; count: number }> {
  return apiRequest<{ models: OllamaModel[]; count: number }>("/system/llm/models", token);
}

export function testOllamaConnection(token?: string): Promise<{
  status: string;
  message: string;
  models: string[];
  count: number;
  configured_model: string;
  model_selection_mode: string;
}> {
  return apiPost("/system/llm/test", {}, token);
}

export function selectOllamaModel(model: string, token?: string): Promise<{ status: string; message: string; model: string }> {
  return apiPost("/system/llm/select", { model }, token);
}

export function testOllamaCompatibility(token?: string): Promise<{
  model: string;
  status: string;
  message: string;
  claims_extracted: number;
}> {
  return apiPost("/system/llm/compatibility-test", {}, token);
}

export async function apiDownload(
  endpoint: string,
  token?: string
): Promise<Blob> {
  const effectiveToken = token ?? getStoredToken();
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: "GET",
      headers: effectiveToken ? { Authorization: `Bearer ${effectiveToken}` } : {},
      cache: "no-store",
    });
  } catch {
    throw new Error("Unable to connect to the server.");
  }
  if (response.status === 401) {
    if (typeof window !== "undefined") {
      localStorage.removeItem("handoveros-token");
      window.location.replace("/login");
    }
    throw new Error("Authentication required. Please sign in again.");
  }
  if (!response.ok) {
    let message = `Unable to load PDF (HTTP ${response.status}).`;
    try {
      const body = await response.json();
      if (typeof body.detail === "string") message = body.detail;
    } catch { /* use status fallback */ }
    throw new Error(message);
  }
  return response.blob();
}

export { getStoredToken };
