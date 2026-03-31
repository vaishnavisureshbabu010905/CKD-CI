"use client";

import { usePathname } from "next/navigation";
import { NavBar } from "@/components/ui/nav";
import { useAuth } from "@/hooks/use-auth";
import { Button } from "@/components/ui/button";
import { PageContainer } from "@/components/layout/page-container";

const PUBLIC_ROUTES = ["/", "/login"];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { user, logout } = useAuth();
  const isPublic = PUBLIC_ROUTES.includes(pathname || "");

  if (isPublic) {
    return <div className="mx-auto flex min-h-screen w-full max-w-7xl items-center px-4 py-6">{children}</div>;
  }

  const desktopWindow = typeof window !== "undefined" ? (window as unknown as { desktopWindow?: { minimize: () => void; maximize: () => void; close: () => void } }).desktopWindow : undefined;

  return (
    <div className="mx-auto grid min-h-screen w-full max-w-7xl grid-cols-1 gap-4 px-4 py-6 lg:grid-cols-[220px_1fr]">
      <aside className="rounded-xl border border-border bg-card/80 p-3">
        <div className="mb-3 px-2 text-xs uppercase tracking-wide text-slate-400">Navigation</div>
        <NavBar vertical />
      </aside>
      <section className="space-y-4">
        <header className="flex items-center justify-between rounded-xl border border-border bg-card/70 px-4 py-3">
          <div>
            <h1 className="text-lg font-semibold">CKD-CI Clinical Platform</h1>
            <div className="text-xs text-slate-400">Unified web and desktop workflow</div>
          </div>
          <div className="flex items-center gap-3 text-sm text-slate-300">
            <span>{user?.email || "Unknown"}</span>
            {desktopWindow && (
              <div className="flex items-center gap-1">
                <Button variant="ghost" size="sm" onClick={() => desktopWindow.minimize()}>_</Button>
                <Button variant="ghost" size="sm" onClick={() => desktopWindow.maximize()}>[]</Button>
                <Button variant="ghost" size="sm" onClick={() => desktopWindow.close()}>X</Button>
              </div>
            )}
            <Button variant="secondary" size="sm" onClick={logout}>Sign out</Button>
          </div>
        </header>
        <PageContainer>
          <div className="space-y-4">{children}</div>
        </PageContainer>
      </section>
    </div>
  );
}
