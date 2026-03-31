const TOKEN_KEY = "ckdci_token";
const COOKIE_NAME = "ckdci_token";

function setCookie(name: string, value: string, maxAgeSeconds: number) {
  if (typeof document === "undefined") return;
  document.cookie = `${name}=${encodeURIComponent(value)}; path=/; max-age=${maxAgeSeconds}; samesite=lax`;
}

function getCookie(name: string): string | null {
  if (typeof document === "undefined") return null;
  const raw = document.cookie
    .split("; ")
    .find((row) => row.startsWith(`${name}=`));
  return raw ? decodeURIComponent(raw.split("=")[1] || "") : null;
}

export function setToken(token: string) {
  if (typeof window !== "undefined") {
    window.localStorage.setItem(TOKEN_KEY, token);
    setCookie(COOKIE_NAME, token, 60 * 60 * 24);
  }
}

export function clearToken() {
  if (typeof window !== "undefined") {
    window.localStorage.removeItem(TOKEN_KEY);
    setCookie(COOKIE_NAME, "", 0);
  }
}

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_KEY) || getCookie(COOKIE_NAME);
}

export function parseJwtExp(token: string): number | null {
  try {
    const payload = token.split(".")[1];
    if (!payload) return null;
    const decoded = JSON.parse(atob(payload));
    return typeof decoded.exp === "number" ? decoded.exp : null;
  } catch {
    return null;
  }
}

export function isTokenExpired(token: string): boolean {
  const exp = parseJwtExp(token);
  if (!exp) return false;
  const now = Math.floor(Date.now() / 1000);
  return exp <= now;
}
