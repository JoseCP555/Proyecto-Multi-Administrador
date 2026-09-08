import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { fileURLToPath, URL } from "node:url";

// Configuración de Vite. La URL de la API se toma de VITE_API_URL
// (ya sea por variables de entorno local o como arg de build en Docker).
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url))
    }
  },
  server: {
    host: true,
    port: 3000,
    // Proxy de desarrollo: /api -> backend (solo en dev; en Docker se usan URLs directas).
    proxy: {
      "/api": {
        target: process.env.VITE_API_PROXY || "http://localhost:8041",
        changeOrigin: true,
        rewrite: (p) => p.replace(/^\/api/, "")
      }
    }
  },
  build: {
    outDir: "dist",
    sourcemap: false
  }
});
