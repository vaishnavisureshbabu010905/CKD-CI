"use client";

import { createContext, useCallback, useContext, useMemo, useState } from "react";

type Toast = { id: number; message: string; type: "success" | "error" | "info" };

type ToastContextValue = {
  notify: (message: string, type?: Toast["type"]) => void;
};

const ToastContext = createContext<ToastContextValue | null>(null);

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const notify = useCallback((message: string, type: Toast["type"] = "info") => {
    const id = Date.now();
    setToasts((prev) => [...prev, { id, message, type }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 3000);
  }, []);

  const value = useMemo(() => ({ notify }), [notify]);

  return (
    <ToastContext.Provider value={value}>
      {children}
      <div className="fixed bottom-4 right-4 z-50 flex w-80 flex-col gap-2">
        {toasts.map((t) => (
          <div
            key={t.id}
            className={`rounded-md border px-3 py-2 text-sm shadow-card ${
              t.type === "success"
                ? "border-emerald-700 bg-emerald-900/60 text-emerald-100"
                : t.type === "error"
                  ? "border-red-700 bg-red-900/60 text-red-100"
                  : "border-slate-700 bg-slate-900/70 text-slate-100"
            }`}
          >
            {t.message}
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToastContext() {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error("useToastContext must be used within ToastProvider");
  return ctx;
}
