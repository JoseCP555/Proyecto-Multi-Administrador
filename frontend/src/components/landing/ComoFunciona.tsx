import { motion } from "framer-motion";
import { Bot, DatabaseZap, UserPlus } from "lucide-react";
import Container from "@/components/ui/Container";
import { contenedor, item, vista } from "./motion";

const pasos = [
  { n: "01", icon: UserPlus, t: "Crea tu cuenta", d: "Regístrate, verifica tu correo con el código y configura tu conjunto en minutos." },
  { n: "02", icon: DatabaseZap, t: "Importa o agrega datos", d: "Residentes, propiedades, conceptos de pago y documentos. Todo queda relacionado." },
  { n: "03", icon: Bot, t: "Administra y pregunta al chatbot", d: "Controla la operación desde el dashboard y consulta cualquier dato en lenguaje natural." },
];

export default function ComoFunciona() {
  return (
    <section id="como-funciona" className="py-24 bg-white">
      <Container>
        <motion.div variants={contenedor} initial="hidden" whileInView="show" viewport={vista} className="text-center max-w-2xl mx-auto">
          <motion.span variants={item} className="text-xs font-bold tracking-widest text-primary-600 uppercase">Cómo funciona</motion.span>
          <motion.h2 variants={item} className="mt-3 text-3xl sm:text-4xl font-extrabold tracking-tight text-dark-100">Empieza en minutos</motion.h2>
        </motion.div>

        <div className="relative mt-16">
          <motion.div
            aria-hidden
            className="hidden lg:block absolute top-9 left-[16%] right-[16%] h-0.5 bg-gradient-to-r from-primary-200 via-primary-500 to-primary-200 origin-left"
            initial={{ scaleX: 0 }} whileInView={{ scaleX: 1 }} viewport={vista} transition={{ duration: 1.2, ease: "easeInOut", delay: 0.3 }}
          />
          <motion.ol variants={contenedor} initial="hidden" whileInView="show" viewport={vista} className="grid gap-10 lg:grid-cols-3">
            {pasos.map(({ n, icon: Icon, t, d }) => (
              <motion.li key={n} variants={item} className="relative text-center px-4">
                <div className="relative mx-auto w-[72px] h-[72px] rounded-full bg-white ring-4 ring-primary-50 shadow-card flex items-center justify-center">
                  <Icon className="w-7 h-7 text-primary-600" />
                  <span className="absolute -top-2 -right-2 w-8 h-8 rounded-full bg-dark-100 text-white text-[11px] font-bold flex items-center justify-center">{n}</span>
                </div>
                <h3 className="mt-6 text-lg font-bold text-dark-100">{t}</h3>
                <p className="mt-2 text-sm text-gray-500 leading-relaxed">{d}</p>
              </motion.li>
            ))}
          </motion.ol>
        </div>
      </Container>
    </section>
  );
}
