"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import {
  LayoutDashboard,
  Users,
  BrainCircuit,
  Bell,
  LineChart,
  ShieldAlert,
  Clock,
  Settings,
} from "lucide-react";

interface NavGroup {
  group: string;
  items: {
    href: string;
    label: string;
    icon: React.ComponentType<{ className?: string }>;
    badge?: string;
  }[];
}

const NAV_GROUPS: NavGroup[] = [
  {
    group: "Clinical Intelligence",
    items: [
      { href: "/command-center", label: "Clinical Overview", icon: LayoutDashboard },
      { href: "/patients", label: "Patient Directory", icon: Users },
      { href: "/prediction", label: "Prediction Studio", icon: BrainCircuit, badge: "CDS" },
    ],
  },
  {
    group: "Patient Surveillance",
    items: [
      { href: "/alerts", label: "Critical Alerts", icon: Bell },
      { href: "/timeline", label: "Longitudinal Trends", icon: Clock },
      { href: "/monitoring", label: "Model Governance", icon: LineChart },
    ],
  },
  {
    group: "Administration",
    items: [
      { href: "/admin", label: "Audit & Access", icon: ShieldAlert },
    ],
  },
];

export function SidebarNav() {
  const pathname = usePathname();

  return (
    <div className="space-y-6">
      {NAV_GROUPS.map((group) => (
        <div key={group.group} className="space-y-1.5">
          <div className="px-3 text-[11px] font-semibold tracking-wider text-text-muted uppercase">
            {group.group}
          </div>
          <div className="space-y-1">
            {group.items.map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.href || (item.href !== "/command-center" && pathname?.startsWith(item.href));
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    "group flex items-center justify-between rounded-lg px-3 py-2 text-xs font-medium transition-all duration-150",
                    isActive
                      ? "bg-primary text-white shadow-subtle"
                      : "text-text-secondary hover:bg-surface-subtle hover:text-text-primary"
                  )}
                >
                  <div className="flex items-center gap-2.5">
                    <Icon
                      className={cn(
                        "h-4 w-4 transition-colors",
                        isActive ? "text-white" : "text-text-muted group-hover:text-text-primary"
                      )}
                    />
                    <span>{item.label}</span>
                  </div>
                  {item.badge && (
                    <span
                      className={cn(
                        "rounded px-1.5 py-0.2 text-[10px] font-semibold uppercase tracking-wider",
                        isActive
                          ? "bg-clinical-teal text-white"
                          : "bg-surface-subtle text-text-muted group-hover:bg-slate-200"
                      )}
                    >
                      {item.badge}
                    </span>
                  )}
                </Link>
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
}

// Retain legacy export signature for backwards compatibility
export function NavBar({ vertical = false }: { vertical?: boolean }) {
  return <SidebarNav />;
}
