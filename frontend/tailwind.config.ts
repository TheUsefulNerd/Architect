import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        midnight: {
          50:  "#e8eaf2",
          100: "#c5c9e0",
          200: "#9ea5cc",
          300: "#7780b8",
          400: "#5a64a9",
          500: "#3d499a",
          600: "#374292",
          700: "#2f3987",
          800: "#27317d",
          900: "#1a226c",
          950: "#0d1117",
        },
        navy: {
          900: "#080c14",
          800: "#0d1220",
          700: "#121829",
          600: "#171f35",
          500: "#1c2640",
          400: "#212e4c",
        },
        accent: {
          blue:   "#3b82f6",
          indigo: "#6366f1",
          violet: "#8b5cf6",
          cyan:   "#06b6d4",
          glow:   "#60a5fa",
        },
        surface: {
          DEFAULT: "#111827",
          raised:  "#1f2937",
          border:  "#1e293b",
          muted:   "#374151",
        },
      },
      fontFamily: {
        display: ["var(--font-display)", "serif"],
        body:    ["var(--font-body)", "sans-serif"],
        mono:    ["var(--font-mono)", "monospace"],
      },
      boxShadow: {
        glow:         "0 0 20px rgba(59,130,246,0.3)",
        "glow-lg":    "0 0 40px rgba(99,102,241,0.4)",
        "glow-sm":    "0 0 10px rgba(59,130,246,0.2)",
        "inner-glow": "inset 0 1px 0 rgba(255,255,255,0.06)",
      },
      animation: {
        "fade-up":    "fadeUp 0.6s ease-out forwards",
        "fade-in":    "fadeIn 0.4s ease-out forwards",
        "pulse-slow": "pulse 3s ease-in-out infinite",
        "shimmer":    "shimmer 2s linear infinite",
        "float":      "float 6s ease-in-out infinite",
        "glow-pulse": "glowPulse 2s ease-in-out infinite",
      },
      keyframes: {
        fadeUp: {
          "0%":   { opacity: "0", transform: "translateY(20px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        fadeIn: {
          "0%":   { opacity: "0" },
          "100%": { opacity: "1" },
        },
        shimmer: {
          "0%":   { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
        float: {
          "0%, 100%": { transform: "translateY(0px)" },
          "50%":      { transform: "translateY(-10px)" },
        },
        glowPulse: {
          "0%, 100%": { boxShadow: "0 0 10px rgba(59,130,246,0.3)" },
          "50%":      { boxShadow: "0 0 25px rgba(99,102,241,0.6)" },
        },
      },
    },
  },
  plugins: [],
};

export default config;