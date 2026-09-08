import type { Variants } from "framer-motion";

/** Variantes compartidas: entrada suave (fade + slide up) con stagger. */
export const contenedor: Variants = {
  hidden: {},
  show: { transition: { staggerChildren: 0.12, delayChildren: 0.05 } },
};

export const item: Variants = {
  hidden: { opacity: 0, y: 40 },
  show: { opacity: 1, y: 0, transition: { duration: 0.6, ease: [0.22, 1, 0.36, 1] } },
};

export const escala: Variants = {
  hidden: { opacity: 0, scale: 0.94, y: 30 },
  show: { opacity: 1, scale: 1, y: 0, transition: { duration: 0.8, ease: [0.22, 1, 0.36, 1] } },
};

export const vista = { once: true, margin: "-80px" } as const;
