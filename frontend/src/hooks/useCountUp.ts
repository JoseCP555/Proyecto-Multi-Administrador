import { useEffect, useRef, useState } from "react";

/**
 * Anima un número desde 0 hasta `objetivo` cuando el elemento es visible.
 * Devuelve el valor actual para mostrarlo con formato de conteo.
 */
export function useCountUp(objetivo: number, durar = 1.2) {
  const [valor, setValor] = useState(0);
  const ref = useRef<HTMLSpanElement>(null);
  const inicioRef = useRef<number | null>(null);
  const activado = useRef(false);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const obs = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && !activado.current) {
          activado.current = true;
          const paso = (ts: number) => {
            if (inicioRef.current === null) inicioRef.current = ts;
            const progreso = Math.min((ts - inicioRef.current) / (durar * 1000), 1);
            // easing ease-out
            const eased = 1 - Math.pow(1 - progreso, 3);
            setValor(Math.round(objetivo * eased));
            if (progreso < 1) requestAnimationFrame(paso);
          };
          requestAnimationFrame(paso);
        }
      },
      { threshold: 0.4 }
    );
    obs.observe(el);
    return () => obs.disconnect();
  }, [objetivo, durar]);

  return { ref, valor };
}
