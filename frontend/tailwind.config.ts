import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        parchment: "#f6f3f1",
        "lake-blue": "#2b59d1",
        "periwinkle-mist": "#cfdaf5",
        "sky-blue": "#a0b5eb",
        mint: "#a7fccd",
        coral: "#ff9473",
        gold: "#ecda98",
        crimson: "#f37a0a",
        "off-black": "#242424",
        ink: "#000000",
        graphite: "#4e4d4d",
        smoke: "#797776",
        ash: "#cecac8",
      },
      fontFamily: {
        mono: [
          "JetBrains Mono",
          "ABC Diatype Mono",
          "ui-monospace",
          "SFMono-Regular",
          "Menlo",
          "Monaco",
          "Consolas",
          "monospace",
        ],
        serif: [
          "Newsreader",
          "Untitled Serif",
          "Georgia",
          "Cambria",
          "Times New Roman",
          "serif",
        ],
        sans: [
          "Untitled Sans",
          "ui-sans-serif",
          "system-ui",
          "-apple-system",
          "sans-serif",
        ],
      },
      borderRadius: {
        card: "40px",
        pill: "9999px",
        btn: "100px",
      },
      boxShadow: {
        ambient: "rgba(0, 0, 0, 0.06) 0px 0px 10px 0px",
      },
    },
  },
  plugins: [],
};

export default config;
