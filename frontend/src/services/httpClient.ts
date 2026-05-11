const API_BASE_URL = normalizeApiBaseUrl(import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000");

interface ApiErrorPayload {
  detail?: {
    code?: string;
    message?: string;
  };
  message?: string;
}

export async function apiGet<T>(path: string): Promise<T> {
  return apiRequest<T>(path, { method: "GET" });
}

export async function apiPost<T>(path: string, body: unknown): Promise<T> {
  return apiRequest<T>(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body)
  });
}

export async function apiDelete<T>(path: string): Promise<T> {
  return apiRequest<T>(path, { method: "DELETE" });
}

async function apiRequest<T>(path: string, init: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, init);
  if (!response.ok) {
    let payload: ApiErrorPayload | undefined;
    try {
      payload = (await response.json()) as ApiErrorPayload;
    } catch {
      payload = undefined;
    }
    const message = payload?.detail?.message ?? payload?.message ?? `HTTP ${response.status}`;
    throw new Error(message);
  }
  return (await response.json()) as T;
}

function normalizeApiBaseUrl(value: string): string {
  const trimmed = value.trim().replace(/\/$/, "");
  if (trimmed.startsWith("http://") || trimmed.startsWith("https://")) {
    return trimmed;
  }
  return `https://${trimmed}`;
}
