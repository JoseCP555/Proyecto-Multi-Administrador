import { motion } from "framer-motion";
import Container from "@/components/ui/Container";
import { useCountUp } from "@/hooks/useCountUp";
import { contenedor, item, vista } from "./motion";

const stats = [
  { prefijo: "+", valor: 1200, sufijo: "", label: "Conjuntos administrados" },
  { prefijo: "", valor: 98, sufijo: "%", label: "Satisfacción" },
  { prefijo: "", valor: 24, sufijo: "/7", label: "Soporte + Chatbot" },
  { prefijo: "-", valor: 40, sufijo: "%", label: "Tiempo de gestión" },
];

function Stat({ prefijo, valor, sufijo, label }: (typeof stats)[number]) {
  const { ref, valor: v } = useCountUp(valor);
  return (
    <motion.div variants={item} className="text-center">
      <span ref={ref} className="block text-4xl sm:text-5xl font-extrabold tracking-tight text-dark-100">
        {prefijo}{v.toLocaleString("es-CO")}<span className="text-primary-500">{sufijo}</span>
      </span>
      <p className="mt-2 text-sm text-gray-500">{label}</p>
    </motion.div>
  );
}

export default function StatsSection() {
  return (
    <section id="stats" className="py-14 bg-white border-y border-gray-100">
      <Container>
        <motion.div variants={contenedor} initial="hidden" whileInView="show" viewport={vista} className="grid grid-cols-2 lg:grid-cols-4 gap-10">
          {stats.map((s) => <Stat key={s.label} {...s} />)}
        </motion.div>
      </Container>
    </section>
  );
}
