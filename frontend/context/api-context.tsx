"use client";

import { createContext, useContext, useMemo } from "react";
import { api } from "@/lib/api";

type ApiContextValue = {
  api: typeof api;
};

const ApiContext = createContext<ApiContextValue | null>(null);

export function ApiProvider({ children }: { children: React.ReactNode }) {
  const value = useMemo(() => ({ api }), []);
  return <ApiContext.Provider value={value}>{children}</ApiContext.Provider>;
}

export function useApiContext() {
  const ctx = useContext(ApiContext);
  if (!ctx) throw new Error("useApiContext must be used within ApiProvider");
  return ctx;
}
