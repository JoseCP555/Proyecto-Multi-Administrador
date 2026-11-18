import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App";
import { AuthProvider } from "@/context/AuthContext";
import { ConjuntoProvider } from "@/context/ConjuntoContext";
import { registrarServiceWorker } from "@/lib/push";
import "./index.css";

// Registra el Service Worker al arrancar para habilitar la instalación PWA
// en Android (Chrome/Edge) e iPhone (Safari) y las notificaciones Push.
if (typeof window !== "undefined" && "serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    void registrarServiceWorker();
  });
}

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <BrowserRouter>
      <AuthProvider>
        <ConjuntoProvider>
          <App />
        </ConjuntoProvider>
      </AuthProvider>
    </BrowserRouter>
  </React.StrictMode>
);
