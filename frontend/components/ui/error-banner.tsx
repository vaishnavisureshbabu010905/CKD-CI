import { cn } from "@/lib/utils";

export function ErrorBanner({ message, className }: { message: string; className?: string }) {
  return (
    <div className={cn("rounded-md border border-red-700/50 bg-red-900/30 px-3 py-2 text-sm text-red-100", className)}>
      {message}
    </div>
  );
}
