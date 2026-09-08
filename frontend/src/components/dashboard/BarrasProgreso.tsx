import { motion } from "framer-motion";

interface Item { label: string; porcentaje: number; color: string }

/** Barras de progreso horizontales redondeadas con porcentaje a la derecha. */
export default function BarrasProgreso({ items, vacio = "Sin datos." }: { items: Item[]; vacio?: string }) {
  if (!items.length) return <p className="text-sm text-gray-400 py-4 text-center">{vacio}</p>;
  return (
    <div className="space-y-4">
      {items.map((it) => (
        <div key={it.label}>
          <div className="flex items-center justify-between text-sm mb-1.5">
            <span className="text-gray-600 truncate pr-3">{it.label}</span>
            <span className="font-bold text-gray-900">{it.porcentaje}%</span>
          </div>
          <div className="h-2.5 rounded-full bg-gray-100 overflow-hidden">
            <motion.div
              className="h-full rounded-full"
              style={{ background: it.color === "gradient" ? "linear-gradient(90deg,#60A5FA,#2563EB)" : it.color }}
              initial={{ width: 0 }}
              animate={{ width: `${it.porcentaje}%` }}
              transition={{ duration: 0.8 }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}
