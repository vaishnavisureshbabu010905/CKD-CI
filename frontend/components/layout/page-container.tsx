import { cn } from "@/lib/utils";

export function PageContainer({ children, className }: { children: React.ReactNode; className?: string }) {
  return <section className={cn("w-full rounded-xl border border-border bg-card/70 p-4 md:p-6", className)}>{children}</section>;
}
