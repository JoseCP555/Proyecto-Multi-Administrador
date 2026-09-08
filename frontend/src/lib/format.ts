// Helpers de formato (es-CO)

export function moneda(valor: number | string | undefined): string {
  const n = Number(valor || 0);
  return "$" + n.toLocaleString("es-CO", { minimumFractionDigits: 0 });
}

export function fecha(iso?: string): string {
  if (!iso) return "—";
  const d = new Date(iso);
  return d.toLocaleDateString("es-CO", { day: "2-digit", month: "short", year: "numeric" });
}

export function fechaHora(iso?: string): string {
  if (!iso) return "—";
  const d = new Date(iso);
  return d.toLocaleString("es-CO", { day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit" });
}

export function tamano(bytes?: number): string {
  if (!bytes) return "—";
  const kb = bytes / 1024;
  if (kb < 1024) return `${kb.toFixed(0)} KB`;
  return `${(kb / 1024).toFixed(1)} MB`;
}

// Primera letra en mayúscula
export function capitalizar(s: string): string {
  return s.charAt(0).toUpperCase() + s.slice(1);
}

export const ROLES: Record<number, { label: string; color: string }> = {
  1: { label: "Súper Admin", color: "bg-purple-100 text-purple-700" },
  2: { label: "Administrador", color: "bg-blue-100 text-blue-700" },
  3: { label: "Residente", color: "bg-emerald-100 text-emerald-700" },
  4: { label: "Tesorería", color: "bg-amber-100 text-amber-700" },
  5: { label: "Seguridad", color: "bg-gray-100 text-gray-700" },
};
