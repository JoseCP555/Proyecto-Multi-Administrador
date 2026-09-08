interface Segmento { label: string; valor: number; color: string }

/** Anillo con total en el centro y leyenda a la derecha. */
export default function DonutChart({ segmentos, total, etiquetaTotal }: { segmentos: Segmento[]; total: number; etiquetaTotal: string }) {
  const R = 54, C = 2 * Math.PI * R;
  let acumulado = 0;
  const suma = segmentos.reduce((a, s) => a + s.valor, 0) || 1;
  return (
    <div className="flex items-center gap-6">
      <div className="relative w-36 h-36 shrink-0">
        <svg viewBox="0 0 140 140" className="w-full h-full -rotate-90">
          <circle cx="70" cy="70" r={R} fill="none" stroke="#F1F5F9" strokeWidth="16" />
          {segmentos.map((s) => {
            const frac = s.valor / suma;
            const dash = `${frac * C} ${C}`;
            const offset = -acumulado * C;
            acumulado += frac;
            return <circle key={s.label} cx="70" cy="70" r={R} fill="none" stroke={s.color} strokeWidth="16" strokeDasharray={dash} strokeDashoffset={offset} strokeLinecap="butt" />;
          })}
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-[11px] text-gray-400">{etiquetaTotal}</span>
          <span className="text-2xl font-extrabold text-gray-900">{total}</span>
        </div>
      </div>
      <ul className="space-y-2.5 text-sm">
        {segmentos.map((s) => (
          <li key={s.label} className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full" style={{ background: s.color }} />
            <span className="text-gray-600">{s.label}</span>
            <span className="ml-auto pl-4 font-semibold text-gray-900">{s.valor}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
