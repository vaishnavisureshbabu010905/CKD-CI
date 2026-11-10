import * as React from "react";
import { cn } from "@/lib/utils";

type ButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary" | "teal" | "outline" | "ghost" | "danger" | "default";
  size?: "sm" | "md" | "lg";
};

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "primary", size = "md", ...props }, ref) => {
    const base =
      "inline-flex items-center justify-center rounded-lg font-medium transition-all duration-150 focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 disabled:opacity-50 disabled:pointer-events-none active:scale-[0.99]";

    const variants: Record<string, string> = {
      primary: "bg-primary text-white hover:bg-primary-dark shadow-subtle",
      default: "bg-primary text-white hover:bg-primary-dark shadow-subtle",
      teal: "bg-clinical-teal text-white hover:bg-clinical-teal-dark shadow-subtle",
      secondary: "bg-surface text-text-primary border border-border hover:bg-surface-subtle shadow-subtle",
      outline: "bg-transparent text-text-primary border border-border hover:bg-surface-subtle",
      ghost: "bg-transparent text-text-secondary hover:text-text-primary hover:bg-surface-subtle",
      danger: "bg-risk-critical text-white hover:bg-red-700 shadow-subtle",
    };

    const sizes: Record<string, string> = {
      sm: "h-8 px-3 text-xs gap-1.5",
      md: "h-9 px-4 text-sm gap-2",
      lg: "h-11 px-5 text-base gap-2.5",
    };

    return (
      <button
        ref={ref}
        className={cn(base, variants[variant], sizes[size], className)}
        {...props}
      />
    );
  }
);
Button.displayName = "Button";
