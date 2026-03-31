"use client";

import { useAuthContext } from "@/context/auth-context";
import { usePathname } from "next/navigation";

const PUBLIC_ROUTES = ["/", "/login"];

export function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { loading, isAuthenticated } = useAuthContext();
  const pathname = usePathname();
  const isPublic = PUBLIC_ROUTES.includes(pathname || "");

  if (loading) {
    return (
      <div className="rounded-md border border-border bg-panel p-4 text-sm text-slate-300">
        Checking session...
      </div>
    );
  }

  if (!isAuthenticated && !isPublic) {
    return null;
  }

  return <>{children}</>;
}
