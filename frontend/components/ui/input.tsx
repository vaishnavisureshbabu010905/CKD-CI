import * as React from "react";
import { cn } from "@/lib/utils";

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  error?: boolean;
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, error, ...props }, ref) => {
    return (
      <input
        ref={ref}
        className={cn(
          "w-full rounded-lg border border-border bg-surface px-3 py-2 text-sm text-text-primary placeholder:text-text-muted transition-colors duration-150 focus:border-clinical-teal focus:outline-none focus:ring-1 focus:ring-clinical-teal disabled:cursor-not-allowed disabled:bg-surface-subtle disabled:text-text-muted",
          error && "border-risk-critical focus:border-risk-critical focus:ring-risk-critical",
          className
        )}
        {...props}
      />
    );
  }
);
Input.displayName = "Input";
