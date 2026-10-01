import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#101828",
        paper: "#F5F7F6",
        brand: { DEFAULT: "#0F6B45", dark: "#0A4F33", tint: "#E6F2EC" },
        alert: { DEFAULT: "#B42318", tint: "#FEF3F2" },
        caution: { DEFAULT: "#B54708", tint: "#FFFAEB" },
        info: { DEFAULT: "#175CD3", tint: "#EFF4FF" },
        dispute: { DEFAULT: "#6941C6", tint: "#F4F3FF" },
      },
      fontFamily: {
        sans: ["system-ui", "-apple-system", "Segoe UI", "Roboto", "Helvetica Neue", "Arial", "sans-serif"],
        display: ["Charter", "Iowan Old Style", "Georgia", "Cambria", "Times New Roman", "serif"],
      },
    },
  },
  plugins: [],
};
export default config;
