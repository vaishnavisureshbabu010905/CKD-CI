import { getToken, clearToken } from "@/lib/auth";

export const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";
export const WS_BASE = process.env.NEXT_PUBLIC_WS_BASE || "ws://localhost:8000";

const API_BASE_CANDIDATES = Array.from(
  new Set(
    [
      API_BASE,
      API_BASE.replace("127.0.0.1", "localhost"),
      API_BASE.replace("localhost", "127.0.0.1"),
      "http://localhost:8000",
      "http://127.0.0.1:8000",
    ].filter(Boolean)
  )
);

type ApiRequestOptions = RequestInit & {
  timeoutMs?: number;
  retries?: number;
  skipAuthRedirect?: boolean;
};

function sleep(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function redirectToLogin() {
  if (typeof window !== "undefined") {
    window.location.href = "/login";
  }
}

function joinUrl(base: string, path: string) {
  const normalizedBase = base.endsWith("/") ? base.slice(0, -1) : base;
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  return `${normalizedBase}${normalizedPath}`;
}

async function readErrorMessage(response: Response): Promise<string> {
  const contentType = response.headers.get("content-type") || "";
  try {
    if (contentType.includes("application/json")) {
      const json = await response.json();
      if (typeof json?.detail === "string") return json.detail;
      if (typeof json?.message === "string") return json.message;
      if (json?.detail) return JSON.stringify(json.detail);
      return JSON.stringify(json);
    }
    const text = await response.text();
    return text || `Request failed with status ${response.status}`;
  } catch {
    return `Request failed with status ${response.status}`;
  }
}

export async function apiRequest<T>(path: string, options: ApiRequestOptions = {}): Promise<T> {
  const timeoutMs = options.timeoutMs ?? 12000;
  const retries = options.retries ?? 1;

  const token = getToken();
  const isFormData = typeof FormData !== "undefined" && options.body instanceof FormData;
  const baseHeaders: HeadersInit = {
    ...(options.headers || {}),
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
  const headers: HeadersInit =
    !isFormData && options.body !== undefined
      ? { "Content-Type": "application/json", ...baseHeaders }
      : baseHeaders;

  let lastError: unknown;

  for (let attempt = 0; attempt <= retries; attempt += 1) {
    const base = API_BASE_CANDIDATES[Math.min(attempt, API_BASE_CANDIDATES.length - 1)] || API_BASE;
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), timeoutMs);
    try {
      const response = await fetch(joinUrl(base, path), {
        ...options,
        headers,
        signal: controller.signal,
        cache: "no-store",
      });
      clearTimeout(timeout);

      if (response.status === 401) {
        clearToken();
        if (!options.skipAuthRedirect) redirectToLogin();
        throw new Error("Session expired. Please sign in again.");
      }

      if (!response.ok) {
        throw new Error(await readErrorMessage(response));
      }

      const contentType = response.headers.get("content-type") || "";
      if (contentType.includes("application/json")) {
        return (await response.json()) as T;
      }
      return (await response.text()) as T;
    } catch (error) {
      clearTimeout(timeout);
      lastError = error;
      const isLastAttempt = attempt === retries && attempt >= API_BASE_CANDIDATES.length - 1;
      if (isLastAttempt) break;
      await sleep(500 * (attempt + 1));
    }
  }

  throw lastError instanceof Error ? lastError : new Error("Request failed");
}

export async function apiDownload(path: string, options: ApiRequestOptions = {}): Promise<Blob> {
  const timeoutMs = options.timeoutMs ?? 12000;
  const retries = options.retries ?? 1;
  const token = getToken();
  const headers: HeadersInit = {
    ...(options.headers || {}),
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };

  let lastError: unknown;
  for (let attempt = 0; attempt <= retries; attempt += 1) {
    const base = API_BASE_CANDIDATES[Math.min(attempt, API_BASE_CANDIDATES.length - 1)] || API_BASE;
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), timeoutMs);
    try {
      const response = await fetch(joinUrl(base, path), {
        ...options,
        method: "GET",
        headers,
        signal: controller.signal,
        cache: "no-store",
      });
      clearTimeout(timeout);

      if (response.status === 401) {
        clearToken();
        if (!options.skipAuthRedirect) redirectToLogin();
        throw new Error("Session expired. Please sign in again.");
      }
      if (!response.ok) {
        throw new Error(await readErrorMessage(response));
      }
      return await response.blob();
    } catch (error) {
      clearTimeout(timeout);
      lastError = error;
      const isLastAttempt = attempt === retries && attempt >= API_BASE_CANDIDATES.length - 1;
      if (isLastAttempt) break;
      await sleep(500 * (attempt + 1));
    }
  }

  throw lastError instanceof Error ? lastError : new Error("Download failed");
}

export const api = {
  get: <T>(path: string, options: ApiRequestOptions = {}) => apiRequest<T>(path, { ...options, method: "GET" }),
  post: <T>(path: string, body?: unknown, options: ApiRequestOptions = {}) =>
    apiRequest<T>(path, { ...options, method: "POST", body: body ? JSON.stringify(body) : undefined }),
  patch: <T>(path: string, body?: unknown, options: ApiRequestOptions = {}) =>
    apiRequest<T>(path, { ...options, method: "PATCH", body: body ? JSON.stringify(body) : undefined }),
  download: (path: string, options: ApiRequestOptions = {}) => apiDownload(path, options),
};
