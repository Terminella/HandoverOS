
const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api";

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
      // Log server errors for diagnostics but show a safe user message.
      if (typeof console !== "undefined") {
        console.error(`Server error ${response.status} for ${endpoint}`, errorBody);
      }
      throw new Error("Something went wrong on the server. Please try again later.");
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
