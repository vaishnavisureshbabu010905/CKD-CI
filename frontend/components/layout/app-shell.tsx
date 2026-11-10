"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { SidebarNav } from "@/components/ui/nav";
import { useAuth } from "@/hooks/use-auth";
import { Button } from "@/components/ui/button";
import { PageContainer } from "@/components/layout/page-container";
import {
  Activity,
  LogOut,
  ShieldCheck,
  Stethoscope,
  ChevronRight,
  Database,
} from "lucide-react";

const PUBLIC_ROUTES = ["/", "/login"];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { user, logout } = useAuth();
  const isPublic = PUBLIC_ROUTES.includes(pathname || "");

  if (isPublic) {
    return <div className="min-h-screen w-full bg-background">{children}</div>;
  }

  return (
    <div className="flex min-h-screen w-full bg-background text-text-primary antialiased">
      {/* Persistent Left Clinical Navigation Sidebar */}
      <aside className="sticky top-0 flex h-screen w-64 flex-col justify-between border-r border-border bg-surface px-4 py-5 shadow-subtle">
        <div className="space-y-6">
          {/* Clinical Brand & Identity Header */}
          <Link href="/command-center" className="flex items-center gap-2.5 px-2">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary text-white shadow-subtle">
              <Activity className="h-5 w-5 text-teal-300" />
            </div>
            <div>
              <div className="flex items-center gap-1.5">
                <span className="text-sm font-bold tracking-tight text-primary">CKD-CI</span>
                <span className="rounded bg-clinical-teal-light px-1 py-0.2 text-[9px] font-semibold text-clinical-teal-dark">
                  CDS v1.0
                </span>
              </div>
              <p className="text-[11px] text-text-muted">Clinical Decision Support</p>
            </div>
          </Link>

          {/* Model Trust & Governance Micro-Badge */}
          <div className="rounded-lg border border-border/80 bg-surface-subtle p-2.5">
            <div className="flex items-center justify-between text-[11px]">
              <span className="flex items-center gap-1 text-text-secondary">
                <ShieldCheck className="h-3.5 w-3.5 text-clinical-teal" />
                Validated Cohort
              </span>
              <span className="font-semibold text-text-primary tabular-nums">N=2,000</span>
            </div>
            <div className="mt-1 flex items-center justify-between text-[10px] text-text-muted">
              <span>Model: Multiclass LR</span>
              <span className="text-risk-normal font-medium">Calibrated</span>
            </div>
          </div>

          {/* Grouped Clinical Navigation */}
          <SidebarNav />
        </div>

        {/* Footer: Active Clinician Profile & Session */}
        <div className="space-y-3 border-t border-border pt-4">
          <div className="flex items-center justify-between px-2">
            <div className="flex items-center gap-2 overflow-hidden">
              <div className="flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-full bg-slate-100 text-xs font-semibold text-primary">
                {user?.email ? user.email.charAt(0).toUpperCase() : "Dr"}
              </div>
              <div className="truncate text-left">
                <div className="truncate text-xs font-medium text-text-primary">
                  {user?.email || "Clinician Session"}
                </div>
                <div className="text-[10px] text-text-muted">Role: Nephrologist</div>
              </div>
            </div>
            <button
              onClick={logout}
              title="Sign Out"
              className="rounded p-1 text-text-muted transition-colors hover:bg-surface-subtle hover:text-risk-critical"
            >
              <LogOut className="h-4 w-4" />
            </button>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex flex-1 flex-col overflow-y-auto">
        {/* Top Clinical Utility Bar */}
        <header className="sticky top-0 z-10 flex h-14 items-center justify-between border-b border-border bg-surface/90 px-6 backdrop-blur-md">
          <div className="flex items-center gap-2 text-xs text-text-muted">
            <Stethoscope className="h-3.5 w-3.5 text-clinical-teal" />
            <span>Nephrology & Neurocognitive Stratification</span>
            <ChevronRight className="h-3 w-3" />
            <span className="font-medium text-text-primary capitalize">
              {pathname?.replace("/", "").replace("-", " ") || "Dashboard"}
            </span>
          </div>

          {/* Real-time Status Badges */}
          <div className="flex items-center gap-3 text-xs">
            <span className="flex items-center gap-1.5 rounded-full border border-emerald-200 bg-risk-normal-bg px-2.5 py-0.5 font-medium text-risk-normal">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
              API Connected
            </span>
            <span className="hidden sm:inline-flex items-center gap-1 text-[11px] text-text-muted tabular-nums">
              <Database className="h-3 w-3" />
              SQLite Persistent (Local)
            </span>
          </div>
        </header>

        {/* Page Content Viewport */}
        <main className="flex-1 px-6 py-6">
          <div className="mx-auto max-w-7xl">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
