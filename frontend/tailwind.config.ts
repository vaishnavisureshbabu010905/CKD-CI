import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        background: "#0f172a",
        panel: "#111827",
        card: "#0b1220",
        accent: "#0ea5e9",
        accent2: "#a855f7",
        border: "#1f2937",
      },
      borderRadius: {
        lg: "12px",
        md: "10px",
        sm: "8px",
      },
      boxShadow: {
        card: "0 10px 40px rgba(0,0,0,0.35)",
      },
    },
  },
  plugins: [],
};

export default config;
