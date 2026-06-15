/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./presentation/templates/**/*.html",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "ui-monospace", "monospace"],
      },
      colors: {
        cyber: {
          500: "#10b981",
          600: "#059669",
        },
      },
    },
  },
  plugins: [],
};
