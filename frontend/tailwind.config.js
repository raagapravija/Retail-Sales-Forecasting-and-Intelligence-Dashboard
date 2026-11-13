/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Off-white surfaces: no pure white anywhere on the page.
        surface: { DEFAULT: "#f7f6f2", sunken: "#efede7", raised: "#faf9f6" },
        ink: { DEFAULT: "#1a1a18", muted: "#52514e", faint: "#85837b" },
        hairline: "#dedbd2",
        // The dashboard's only colours: actuals, forecast, and up/down change.
        actual: "#1f5fa8",
        forecast: "#c4561d",
        up: "#2e7a4c",
        down: "#b3392f",
      },
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "-apple-system", "Segoe UI", "sans-serif"],
        mono: ["ui-monospace", "SFMono-Regular", "Menlo", "monospace"],
      },
    },
  },
  plugins: [],
};
