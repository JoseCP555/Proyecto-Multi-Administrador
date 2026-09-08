import type { ReactNode } from "react";

const colores: Record<string, string> = {
  success: "bg-emerald-100 text-emerald-700",
  info: "bg-blue-100 text-blue-700",
  warning: "bg-amber-100 text-amber-700",
  danger: "bg-red-100 text-red-700",
  neutral: "bg-gray-100 text-gray-600",
  purple: "bg-purple-100 text-purple-700",
};

export default function Badge({
  children,
  color = "neutral",
}: {
  children: ReactNode;
  color?: keyof typeof colores | string;
}) {
  return (
    <span className={`badge ${colores[color] || colores.neutral}`}>{children}</span>
  );
}

// Mapea el estado de una entidad a un color de Badge.
export function estadoColor(estado: string): string {
  switch (estado) {
    case "pagado":
    case "completada":
    case "ocupado":
    case "activo":
    case "activa":
      return "success";
    case "vencido":
    case "critica":
    case "rechazada":
      return "danger";
    case "pendiente":
    case "en_proceso":
    case "mantenimiento":
    case "arrendado":
      return "warning";
    case "vacio":
    case "cancelado":
      return "neutral";
    default:
      return "info";
  }
}
