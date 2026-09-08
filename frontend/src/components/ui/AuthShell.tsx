import type { ReactNode } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import logoUrl from "@/lib/logo";

// Estructura visual compartida para Login / Registro / Restablecer.
export default function AuthShell({
  titulo,
  subtitulo,
  children,
  footer,
}: {
  titulo: string;
  subtitulo?: string;
  children: ReactNode;
  footer?: ReactNode;
}) {
  return (
    <div className="min-h-screen flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-md">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          {/* Logo */}
          <Link to="/" className="flex items-center justify-center gap-2 mb-6">
            <img src={logoUrl} alt="Multi-Admin" className="w-14 h-14 object-contain" />
            <span className="text-2xl font-extrabold text-gray-900 tracking-tight">Multi-Administrador</span>
          </Link>

          {/* Tarjeta */}
          <div className="bg-white rounded-4xl shadow-shell p-8">
            <h1 className="text-2xl font-bold text-gray-800 text-center">{titulo}</h1>
            {subtitulo && (
              <p className="text-sm text-gray-500 text-center mt-1 mb-6">{subtitulo}</p>
            )}
            {children}
          </div>

          {footer && <div className="text-center mt-6 text-sm text-gray-500">{footer}</div>}
        </motion.div>
      </div>
    </div>
  );
}
