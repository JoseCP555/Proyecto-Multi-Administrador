import { motion } from "framer-motion";

interface Punto { mes: string; valor: number }

/** 1.250.000 → "$1,25M", 37.500 → "$37,5K". */
function abreviar(v: number): string {
  if (v >= 1_000_000) return `$${(v / 1_000_000).toFixed(v % 1_000_000 ? 2 : 0).replace(".", ",")}M`;
  if (v >= 1_000) return `$${(v / 1_000).toFixed(v % 1_000 ? 1 : 0).replace(".", ",")}K`;
  return `$${Math.round(v)}`;
}

/** Gráfico de área con relleno degradado (azul → transparente) y etiqueta flotante en el pico. */
export default function AreaChart({ datos, etiqueta, cargando }: { datos: Punto[]; etiqueta?: string; cargando?: boolean }) {
  const W = 720, H = 260, PL = 64, PR = 16, PT = 28, PB = 32;
  if (!datos.length) {
    return <p className="text-gray-400 text-sm h-52 flex items-center justify-center">{cargando ? "Cargando..." : "Sin datos."}</p>;
  }
  const max = Math.max(...datos.map((d) => d.valor), 1);
  const iw = W - PL - PR, ih = H - PT - PB;
  const x = (i: number) => PL + (datos.length === 1 ? iw / 2 : (i / (datos.length - 1)) * iw);
  const y = (v: number) => PT + ih - (v / max) * ih;

  // Curva suave (Catmull-Rom → Bézier)
  const pts = datos.map((d, i) => [x(i), y(d.valor)] as const);
  let path = `M ${pts[0][0]} ${pts[0][1]}`;
  for (let i = 0; i < pts.length - 1; i++) {
    const p0 = pts[i - 1] ?? pts[i], p1 = pts[i], p2 = pts[i + 1], p3 = pts[i + 2] ?? p2;
    const c1x = p1[0] + (p2[0] - p0[0]) / 6, c1y = p1[1] + (p2[1] - p0[1]) / 6;
    const c2x = p2[0] - (p3[0] - p1[0]) / 6, c2y = p2[1] - (p3[1] - p1[1]) / 6;
    path += ` C ${c1x} ${c1y}, ${c2x} ${c2y}, ${p2[0]} ${p2[1]}`;
  }
  const area = `${path} L ${pts[pts.length - 1][0]} ${PT + ih} L ${pts[0][0]} ${PT + ih} Z`;
  const picoIdx = datos.reduce((b, d, i, arr) => (d.valor > arr[b].valor ? i : b), 0);
  const ticks = [0, 0.25, 0.5, 0.75, 1];

  return (
    <div className="w-full overflow-x-auto">
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full h-auto min-w-[480px]">
        <defs>
          <linearGradient id="areaFill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#2563EB" stopOpacity="0.35" />
            <stop offset="100%" stopColor="#2563EB" stopOpacity="0" />
          </linearGradient>
        </defs>
        {ticks.map((t) => (
          <g key={t}>
            <line x1={PL} x2={W - PR} y1={PT + ih - t * ih} y2={PT + ih - t * ih} stroke="#F1F5F9" strokeDasharray="4 4" />
            <text x={PL - 8} y={PT + ih - t * ih + 4} textAnchor="end" fontSize="11" fill="#94A3B8">
              {t === 0 ? "0" : abreviar(max * t)}
            </text>
          </g>
        ))}
        <motion.path d={area} fill="url(#areaFill)" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.8 }} />
        <motion.path d={path} fill="none" stroke="#2563EB" strokeWidth="3" strokeLinecap="round"
          initial={{ pathLength: 0 }} animate={{ pathLength: 1 }} transition={{ duration: 1 }} />
        {datos.map((d, i) => (
          <text key={d.mes} x={x(i)} y={H - 8} textAnchor="middle" fontSize="11" fill="#94A3B8">{d.mes}</text>
        ))}
        {/* Punto y etiqueta en el pico */}
        <circle cx={x(picoIdx)} cy={y(datos[picoIdx].valor)} r="6" fill="#fff" stroke="#2563EB" strokeWidth="3" />
        {etiqueta && (
          <g transform={`translate(${Math.min(Math.max(x(picoIdx), PL + 40), W - PR - 40)}, ${Math.max(y(datos[picoIdx].valor) - 22, 14)})`}>
            <rect x="-34" y="-12" width="68" height="24" rx="12" fill="#111111" />
            <text textAnchor="middle" y="4" fontSize="11" fontWeight="700" fill="#fff">{etiqueta}</text>
          </g>
        )}
      </svg>
    </div>
  );
}
