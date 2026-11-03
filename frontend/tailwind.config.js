/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        // Paleta idéntica a la del dashboard.
        // `primary` se lee de variables CSS (--pc-*): por defecto son el azul
        // de siempre (ver :root en index.css) y, al abrir un conjunto, el
        // layout las cambia por el color de ese conjunto.
        primary: {
          50: "rgb(var(--pc-50) / <alpha-value>)",
          100: "rgb(var(--pc-100) / <alpha-value>)",
          200: "rgb(var(--pc-200) / <alpha-value>)",
          300: "rgb(var(--pc-300) / <alpha-value>)",
          500: "rgb(var(--pc-500) / <alpha-value>)",
          600: "rgb(var(--pc-600) / <alpha-value>)",
          700: "rgb(var(--pc-700) / <alpha-value>)"
        },
        dark: {
          100: "#111111",
          200: "#0a0a0a"
        },
        surface: "#f6f7fb",
        lilac: {
          100: "#E8E0FF",
          200: "#C5B8F5"
        },
        gray: {
          50: "#f8fafc",
          100: "#f1f5f9",
          200: "#e5e7eb",
          300: "#cbd5e1",
          400: "#94a3b8",
          500: "#64748b",
          600: "#475569",
          800: "#1e293b"
        },
        success: "#10b981",
        warning: "#f59e0b",
        danger: "#ef4444"
      },
      fontFamily: {
        sans: ["Inter", "Poppins", "system-ui", "-apple-system", "Segoe UI", "sans-serif"]
      },
      boxShadow: {
        card: "0 2px 12px rgba(17,24,39,0.05)",
        "card-hover": "0 10px 30px rgb(var(--pc-500) / 0.10)",
        shell: "0 30px 80px rgba(76,29,149,0.18)",
        pill: "0 6px 18px rgb(var(--pc-500) / 0.30)"
      },
      borderRadius: {
        DEFAULT: "14px",
        "2xl": "20px",
        "3xl": "28px",
        "4xl": "32px"
      }
    }
  },
  plugins: []
};
