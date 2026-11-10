import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Base surfaces
        background: "#F8FAFC",
        surface: "#FFFFFF",
        "surface-subtle": "#F1F5F9",
        "surface-hover": "#E2E8F0",
        
        // Brand & Clinical Accents
        primary: {
          DEFAULT: "#16324F", // Deep Navy
          dark: "#0E2135",
          light: "#2A4B6E",
        },
        clinical: {
          teal: "#0F766E", // Clinical Teal
          "teal-light": "#CCFBF1",
          "teal-dark": "#115E59",
        },
        
        // Borders & Dividers
        border: "#E2E8F0",
        "border-subtle": "#CBD5E1",
        
        // Text hierarchy
        "text-primary": "#0F172A",
        "text-secondary": "#475569",
        "text-muted": "#94A3B8",

        // Medical Tri-State & Risk Semantics
        risk: {
          normal: "#059669",     // Emerald 600
          "normal-bg": "#ECFDF5",
          moderate: "#D97706",   // Amber 600
          "moderate-bg": "#FFFBEB",
          critical: "#DC2626",   // Red 600
          "critical-bg": "#FEF2F2",
          elevated: "#EA580C",   // Orange 600
          "elevated-bg": "#FFF7ED",
        },
      },
      fontFamily: {
        sans: [
          "Inter",
          "-apple-system",
          "BlinkMacSystemFont",
          "Segoe UI",
          "Roboto",
          "sans-serif",
        ],
        mono: ["JetBrains Mono", "Menlo", "Courier New", "monospace"],
      },
      borderRadius: {
        xl: "12px",
        lg: "8px",
        md: "6px",
        sm: "4px",
      },
      boxShadow: {
        subtle: "0 1px 3px 0 rgba(0, 0, 0, 0.05), 0 1px 2px 0 rgba(0, 0, 0, 0.03)",
        card: "0 1px 3px 0 rgba(0, 0, 0, 0.04), 0 4px 12px 0 rgba(0, 0, 0, 0.03)",
        elevated: "0 4px 6px -1px rgba(0, 0, 0, 0.07), 0 10px 24px -3px rgba(0, 0, 0, 0.06)",
        modal: "0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)",
      },
    },
  },
  plugins: [],
};

export default config;
