import { cn } from "@/lib/utils";

type Status = "stable" | "monitor" | "attention" | "critical";

const map: Record<Status, string> = {
  stable: "bg-emerald-500/20 text-emerald-100 border-emerald-500/30",
  monitor: "bg-sky-500/20 text-sky-100 border-sky-500/30",
  attention: "bg-amber-500/20 text-amber-100 border-amber-500/30",
  critical: "bg-red-500/20 text-red-100 border-red-500/30",
};

export function StatusBadge({ status, className }: { status: Status; className?: string }) {
  return <span className={cn("inline-flex rounded-full border px-2.5 py-1 text-xs font-semibold uppercase", map[status], className)}>{status}</span>;
}
