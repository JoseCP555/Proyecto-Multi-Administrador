import { motion } from "framer-motion";
import { ArrowUpRight, ArrowDownRight } from "lucide-react";
import type { LucideIcon } from "lucide-react";

/**
 * Tarjeta de métrica. `destacada` la pinta en azul intenso con texto blanco
 * (como la card "Earning" del diseño); el resto va en blanco con borde sutil.
 */
export default function StatCard({
  titulo,
  valor,
  icono: Icono,
  color = "primary",
  indicador,
  subida = true,
  destacada = false,
}: {
  titulo: string;
  valor: string;
  icono: LucideIcon;
  color?: "primary" | "success" | "warning" | "danger" | "purple";
  indicador?: string;
  subida?: boolean;
  destacada?: boolean;
}) {
  const colores: Record<string, string> = {
    primary: "bg-primary-50 text-primary-500",
    success: "bg-emerald-50 text-emerald-600",
    warning: "bg-amber-50 text-amber-600",
    danger: "bg-red-50 text-red-500",
    purple: "bg-purple-50 text-purple-600",
  };
  const Flecha = subida ? ArrowUpRight : ArrowDownRight;

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35 }}
      className={`rounded-3xl p-6 transition-all duration-200 ${
        destacada
          ? "bg-primary-500 text-white shadow-pill"
          : "bg-white border border-gray-100 shadow-card hover:shadow-card-hover"
      }`}
    >
      <div className="flex items-center gap-4">
        <div
          className={`w-12 h-12 rounded-full flex items-center justify-center shrink-0 ${
            destacada ? "bg-white/15 text-white" : colores[color]
          }`}
        >
          <Icono className="w-5 h-5" />
        </div>
        <div className="min-w-0">
          <p className={`text-sm font-medium ${destacada ? "text-white/80" : "text-gray-500"}`}>{titulo}</p>
          <p className={`text-3xl font-extrabold tracking-tight mt-0.5 ${destacada ? "text-white" : "text-gray-900"}`}>{valor}</p>
        </div>
      </div>
      {indicador && (
        <p
          className={`mt-4 text-xs font-medium flex items-center gap-1 ${
            destacada ? "text-white/90" : subida ? "text-emerald-600" : "text-red-500"
          }`}
        >
          <Flecha className="w-3.5 h-3.5" /> {indicador}
        </p>
      )}
    </motion.div>
  );
}
