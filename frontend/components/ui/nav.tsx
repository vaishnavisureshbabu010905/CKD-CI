"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

const links = [
  { href: "/command-center", label: "Command" },
  { href: "/patients", label: "Patients" },
  { href: "/chat", label: "Chat" },
  { href: "/alerts", label: "Alerts" },
  { href: "/prediction", label: "Predict" },
  { href: "/timeline", label: "Timeline" },
  { href: "/admin", label: "Admin" },
  { href: "/monitoring", label: "Monitoring" },
];

export function NavBar({ vertical = false }: { vertical?: boolean }) {
  const pathname = usePathname();
  return (
    <nav className={cn("gap-2", vertical ? "grid" : "flex overflow-x-auto pb-2")}>
      {links.map((link) => (
        <Link
          key={link.href}
          href={link.href}
          className={cn(
            "rounded-md px-3 py-2 text-sm font-semibold text-slate-200 hover:bg-slate-800",
            pathname?.startsWith(link.href) ? "bg-slate-800 text-white" : "bg-panel"
          )}
        >
          {link.label}
        </Link>
      ))}
    </nav>
  );
}
