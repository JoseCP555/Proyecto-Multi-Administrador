import { motion } from "framer-motion";
import { Activity, Bot, ShieldCheck } from "lucide-react";
import Container from "@/components/ui/Container";
import DashboardMock from "./DashboardMock";
import { contenedor, escala, item, vista } from "./motion";

const etiquetas = [
  { icon: Bot, t: "Chatbot con datos reales", pos: "-top-4 left-4 sm:left-10", delay: 0.6 },
  { icon: Activity, t: "Estadísticas en vivo", pos: "top-1/3 -right-3 sm:-right-8", delay: 0.8 },
  { icon: ShieldCheck, t: "Roles y permisos", pos: "-bottom-4 left-1/4", delay: 1.0 },
];

export default function DashboardPreview() {
  return (
    <section id="dashboard" className="relative py-24 overflow-hidden bg-gradient-to-b from-white via-[#EEF2FF] to-white">
      <div aria-hidden className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-[900px] h-[500px] rounded-full bg-primary-500/10 blur-3xl" />
      <Container className="relative">
        <motion.div variants={contenedor} initial="hidden" whileInView="show" viewport={vista} className="text-center max-w-2xl mx-auto">
          <motion.span variants={item} className="text-xs font-bold tracking-widest text-primary-600 uppercase">Dashboard</motion.span>
          <motion.h2 variants={item} className="mt-3 text-3xl sm:text-4xl font-extrabold tracking-tight text-dark-100">
            Un dashboard pensado para administradores reales
          </motion.h2>
          <motion.p variants={item} className="mt-4 text-gray-500">
            Lo que importa, de un vistazo: recaudo, cartera, mantenimientos, eventos y tu asistente.
          </motion.p>
        </motion.div>

        <motion.div variants={escala} initial="hidden" whileInView="show" viewport={vista} className="relative mt-14 max-w-4xl mx-auto">
          <DashboardMock />
          {etiquetas.map(({ icon: Icon, t, pos, delay }) => (
            <motion.span
              key={t}
              initial={{ opacity: 0, y: 12 }} whileInView={{ opacity: 1, y: 0 }} viewport={vista} transition={{ delay, duration: 0.5 }}
              className={`absolute ${pos} inline-flex items-center gap-2 rounded-full bg-dark-100 text-white text-xs font-semibold px-3.5 py-2 shadow-lg`}
            >
              <Icon className="w-3.5 h-3.5 text-primary-200" /> {t}
            </motion.span>
          ))}
        </motion.div>
      </Container>
    </section>
  );
}
