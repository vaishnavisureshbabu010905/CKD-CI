"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { clearToken, getToken, isTokenExpired, setToken } from "@/lib/auth";

type User = {
  email: string;
  role: string;
};

type AuthContextValue = {
  token: string | null;
  user: User | null;
  isAuthenticated: boolean;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
};

const AuthContext = createContext<AuthContextValue | null>(null);

function parseJwt(token: string): User | null {
  try {
    const payload = JSON.parse(atob(token.split(".")[1] || ""));
    return {
      email: payload.sub || "",
      role: payload.role || "doctor",
    };
  } catch {
    return null;
  }
}

const PUBLIC_ROUTES = ["/", "/login"];

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [token, setTokenState] = useState<string | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const pathname = usePathname();
  const router = useRouter();

  useEffect(() => {
    const existing = getToken();
    if (existing && !isTokenExpired(existing)) {
      setTokenState(existing);
      setUser(parseJwt(existing));
    } else {
      clearToken();
      setTokenState(null);
      setUser(null);
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    if (loading) return;
    const isPublic = PUBLIC_ROUTES.includes(pathname || "");
    if (!token && !isPublic) {
      router.replace("/login");
    }
    if (token && pathname === "/login") {
      router.replace("/command-center");
    }
  }, [loading, pathname, token, router]);

  const login = useCallback(async (email: string, password: string) => {
    const normalizedEmail = email.trim();
    const normalizedPassword = password;
    if (!normalizedEmail || !normalizedPassword.trim()) {
      throw new Error("Email and password are required");
    }

    const response = await api.post<{ access_token: string; token_type: string }>(
      "/auth/login",
      { email: normalizedEmail, password: normalizedPassword },
      { skipAuthRedirect: true }
    );
    setToken(response.access_token);
    setTokenState(response.access_token);
    setUser(parseJwt(response.access_token));
  }, []);

  const logout = useCallback(() => {
    clearToken();
    setTokenState(null);
    setUser(null);
    router.replace("/login");
  }, [router]);

  const value = useMemo<AuthContextValue>(
    () => ({
      token,
      user,
      isAuthenticated: Boolean(token),
      loading,
      login,
      logout,
    }),
    [token, user, loading, login, logout]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuthContext() {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuthContext must be used within AuthProvider");
  }
  return ctx;
}
