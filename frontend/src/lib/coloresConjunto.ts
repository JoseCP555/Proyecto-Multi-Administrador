import type { CSSProperties } from "react";

/**
 * Paleta de colores por conjunto.
 *
 * Antes el color se deducía solo de la posición del conjunto en la lista.
 * Ahora cada conjunto guarda su propio color en `conjuntos.color`:
 *  - el id de un color de la paleta (`azul`, `verde`, `ambar`, `rosa`,
 *    `violeta`, `cian`), o
 *  - un hexadecimal libre (`#RRGGBB`) elegido en el modal.
 *
 * `NULL` / sin valor = automático: se usa el color que le toca por posición,
 * que es exactamente el comportamiento anterior (así las bases ya existentes
 * siguen viéndose igual).
 *
 * Cada `ColorConjunto` trae:
 *  - `hex`, `gradiente`, `fondo`, `texto`: valores CSS listos para `style`.
 *  - `rgb`: el color en formato "R G B" para las variables CSS `--pc-*`
 *    que usa el color `primary` de Tailwind dentro del conjunto.
 */
export type ClaveEscala = 50 | 100 | 200 | 300 | 500 | 600 | 700;
export type EscalaRGB = Record<ClaveEscala, string>;
export type EscalaHex = Record<ClaveEscala, string>;

export interface ColorConjunto {
  id: string;
  nombre: string;
  hex: string;
  gradiente: string;
  fondo: string;
  texto: string;
  sombras: EscalaHex;
  rgb: EscalaRGB;
  personalizado: boolean;
}

type Triple = [number, number, number];
const CLAVES: ClaveEscala[] = [50, 100, 200, 300, 500, 600, 700];

function hexATriple(hex: string): Triple {
  const h = hex.replace("#", "");
  return [parseInt(h.slice(0, 2), 16), parseInt(h.slice(2, 4), 16), parseInt(h.slice(4, 6), 16)];
}

function tripleAHex([r, g, b]: Triple): string {
  const p = (n: number) => Math.max(0, Math.min(255, Math.round(n))).toString(16).padStart(2, "0");
  return `#${p(r)}${p(g)}${p(b)}`;
}

function aRgb(hex: string): string {
  return hexATriple(hex).join(" ");
}

/** Mezcla dos colores. `peso` = proporción del segundo. */
function mezclar(a: Triple, b: Triple, peso: number): string {
  return tripleAHex([
    a[0] * (1 - peso) + b[0] * peso,
    a[1] * (1 - peso) + b[1] * peso,
    a[2] * (1 - peso) + b[2] * peso,
  ]);
}

const BLANCO: Triple = [255, 255, 255];
const NEGRO: Triple = [17, 24, 39];

function construir(id: string, nombre: string, sombras: EscalaHex, personalizado = false): ColorConjunto {
  const rgb = Object.fromEntries(
    CLAVES.map((k) => [k, aRgb(sombras[k])]),
  ) as EscalaRGB;
  return {
    id,
    nombre,
    hex: sombras[500],
    gradiente: `linear-gradient(135deg, ${sombras[500]} 0%, ${sombras[700]} 100%)`,
    fondo: sombras[50],
    texto: sombras[700],
    sombras,
    rgb,
    personalizado,
  };
}

/** Construye una escala tipo Tailwind (50…700) a partir de un color libre. */
export function escalaDesdeHex(hex: string): EscalaHex {
  const base = hexATriple(hex);
  return {
    50: mezclar(base, BLANCO, 0.92),
    100: mezclar(base, BLANCO, 0.82),
    200: mezclar(base, BLANCO, 0.64),
    300: mezclar(base, BLANCO, 0.42),
    500: tripleAHex(base),
    600: mezclar(base, NEGRO, 0.18),
    700: mezclar(base, NEGRO, 0.34),
  };
}

export const COLORES_CONJUNTO: ColorConjunto[] = [
  construir("azul", "Azul", {
    50: "#eff6ff", 100: "#dbeafe", 200: "#bfdbfe", 300: "#93c5fd",
    500: "#3b82f6", 600: "#2563eb", 700: "#1e40af",
  }),
  construir("verde", "Verde", {
    50: "#ecfdf5", 100: "#d1fae5", 200: "#a7f3d0", 300: "#6ee7b7",
    500: "#10b981", 600: "#059669", 700: "#047857",
  }),
  construir("ambar", "Ámbar", {
    50: "#fffbeb", 100: "#fef3c7", 200: "#fde68a", 300: "#fcd34d",
    500: "#f59e0b", 600: "#d97706", 700: "#b45309",
  }),
  construir("rosa", "Rosa", {
    50: "#fff1f2", 100: "#ffe4e6", 200: "#fecdd3", 300: "#fda4af",
    500: "#f43f5e", 600: "#e11d48", 700: "#be123c",
  }),
  construir("violeta", "Violeta", {
    50: "#f5f3ff", 100: "#ede9fe", 200: "#ddd6fe", 300: "#c4b5fd",
    500: "#8b5cf6", 600: "#7c3aed", 700: "#6d28d9",
  }),
  construir("cian", "Cian", {
    50: "#ecfeff", 100: "#cffafe", 200: "#a5f3fc", 300: "#67e8f9",
    500: "#06b6d4", 600: "#0891b2", 700: "#0e7490",
  }),
];

const HEX = /^#([0-9a-f]{6}|[0-9a-f]{3})$/i;

/** Normaliza lo escrito por el usuario: `#abc` -> `#aabbcc`. Devuelve null si no es válido. */
export function normalizarColor(valor: string): string | null {
  const v = valor.trim().toLowerCase();
  if (!v) return null;
  if (COLORES_CONJUNTO.some((c) => c.id === v)) return v;
  const conGato = v.startsWith("#") ? v : `#${v}`;
  if (!HEX.test(conGato)) return null;
  if (conGato.length === 4) {
    return `#${conGato[1]}${conGato[1]}${conGato[2]}${conGato[2]}${conGato[3]}${conGato[3]}`.toLowerCase();
  }
  return conGato.toLowerCase();
}

/** Resuelve el color guardado en un conjunto (o el automático por posición). */
export function resolverColor(valor?: string | null, indice = 0): ColorConjunto {
  const v = (valor ?? "").trim().toLowerCase();
  if (v) {
    const dePaleta = COLORES_CONJUNTO.find((c) => c.id === v);
    if (dePaleta) return dePaleta;
    const hex = normalizarColor(v);
    if (hex && hex.startsWith("#")) {
      return construir(hex, "Personalizado", escalaDesdeHex(hex), true);
    }
  }
  return COLORES_CONJUNTO[(indice < 0 ? 0 : indice) % COLORES_CONJUNTO.length];
}

/** Color que le corresponde a un conjunto (guardado o automático). */
export function colorDeConjunto(
  conjuntos: { id: number; color?: string | null }[],
  id: number | null | undefined,
): ColorConjunto {
  const i = id == null ? -1 : conjuntos.findIndex((c) => c.id === id);
  return resolverColor(conjuntos[i]?.color, i < 0 ? 0 : i);
}

/** Siguiente color de la paleta, para sugerirlo al crear un conjunto. */
export function colorSugerido(cantidad: number): string {
  return COLORES_CONJUNTO[Math.max(0, cantidad) % COLORES_CONJUNTO.length].id;
}

/**
 * Variables CSS con el color del conjunto, para aplicar como `style` en el
 * contenedor del dashboard: todo lo que usa el color `primary` (botones,
 * menú activo, barra de búsqueda, tarjetas destacadas, gráficas…) toma
 * automáticamente el color del conjunto abierto.
 */
export function temaConjunto(
  conjuntos: { id: number; color?: string | null }[],
  id: number | null | undefined,
): CSSProperties {
  const { rgb } = colorDeConjunto(conjuntos, id);
  return {
    "--pc-50": rgb[50],
    "--pc-100": rgb[100],
    "--pc-200": rgb[200],
    "--pc-300": rgb[300],
    "--pc-500": rgb[500],
    "--pc-600": rgb[600],
    "--pc-700": rgb[700],
  } as CSSProperties;
}
