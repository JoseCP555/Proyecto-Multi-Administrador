import { useRef, useEffect } from "react";
import { useAnimation, useInView } from "framer-motion";

/**
 * Hook de animación al scroll:
 * Devuelve un ref y los controles de animación. Cuando el elemento
 * entra en el viewport (una sola vez), dispara la animación "animate".
 */
export function useScrollAnimation() {
  const ref = useRef<HTMLDivElement>(null);
  const controls = useAnimation();
  const inView = useInView(ref, { once: true, margin: "-80px" });

  useEffect(() => {
    if (inView) {
      controls.start("animate");
    }
  }, [inView, controls]);

  return { ref, controls };
}
