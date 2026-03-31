"use client";

import { ApiProvider } from "@/context/api-context";
import { AuthProvider } from "@/context/auth-context";
import { ToastProvider } from "@/context/toast-context";

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <ApiProvider>
      <AuthProvider>
        <ToastProvider>{children}</ToastProvider>
      </AuthProvider>
    </ApiProvider>
  );
}
