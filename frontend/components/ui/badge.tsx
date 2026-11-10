import * as React from "react";
import { cn } from "@/lib/utils";

type BadgeVariant = "default" | "normal" | "moderate" | "critical" | "elevated" | "outline" | "teal";

export function Badge({
  className,
  variant = "default",
  children,
}: {
  className?: string;
  variant?: BadgeVariant;
  children: React.ReactNode;
}) {
  const variants: Record<BadgeVariant, string> = {
    default: "bg-surface-subtle text-text-secondary border-border",
    normal: "bg-risk-normal-bg text-risk-normal border-emerald-200 font-medium",
    moderate: "bg-risk-moderate-bg text-risk-moderate border-amber-200 font-medium",
    elevated: "bg-risk-elevated-bg text-risk-elevated border-orange-200 font-medium",
    critical: "bg-risk-critical-bg text-risk-critical border-red-200 font-semibold",
    teal: "bg-clinical-teal-light text-clinical-teal-dark border-teal-200 font-medium",
    outline: "bg-transparent text-text-secondary border-border",
  };

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs tracking-tight tabular-nums transition-colors",
        variants[variant],
        className
      )}
    >
      {children}
    </span>
  );
}
