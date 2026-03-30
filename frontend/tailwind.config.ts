import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        navy: "#1a1a2e",
        "navy-light": "#16213e",
        "warm-white": "#fafaf9",
        teal: "#06d6a0",
        coral: "#ef476f",
        amber: "#ffd166",
      },
      fontFamily: {
        sans: ["Plus Jakarta Sans", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [require("@tailwindcss/typography")],
};

export default config;
