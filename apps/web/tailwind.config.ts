import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        forge: {
          50: "#eef4ff",
          500: "#4f6bed",
          600: "#3a53d0",
          700: "#2f43a8",
        },
      },
    },
  },
  plugins: [],
};

export default config;
