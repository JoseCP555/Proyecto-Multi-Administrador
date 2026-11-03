import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App";
import { AuthProvider } from "@/context/AuthContext";
import { ConjuntoProvider } from "@/context/ConjuntoContext";
import "./index.css";

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
