/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        // Paleta idéntica a la del dashboard
        primary: {
          50: "#eff6ff",
          100: "#dbeafe",
          200: "#bfdbfe",
          500: "#2563eb",
          600: "#1d4ed8",
          700: "#1e40af"
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
        "card-hover": "0 10px 30px rgba(37,99,235,0.10)",
        shell: "0 30px 80px rgba(76,29,149,0.18)",
        pill: "0 6px 18px rgba(37,99,235,0.30)"
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
