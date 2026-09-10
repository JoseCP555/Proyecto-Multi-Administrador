import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { ArrowRight, Bot, CheckCircle2, ChevronDown, PlayCircle, ShieldCheck, Sparkles, Wallet } from "lucide-react";
import Button from "@/components/ui/Button";
import DashboardMock from "./DashboardMock";
import { contenedor, item } from "./motion";

const flotante = (delay: number) => ({
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: [0, -6, 0] },
  transition: { opacity: { delay, duration: 0.5 }, y: { delay, duration: 5, repeat: Infinity, ease: "easeInOut" } },
});

export default function HeroSection() {
  const [esEscritorio, setEsEscritorio] = useState(false);
  useEffect(() => {
    const mq = window.matchMedia("(min-width: 1024px)");
    const f = () => setEsEscritorio(mq.matches);
    f(); mq.addEventListener("change", f);
    return () => mq.removeEventListener("change", f);
  }, []);
  return (
    <section id="inicio" className="relative overflow-x-clip overflow-hidden pt-28 pb-20 lg:pt-40 lg:pb-28">
      {/* Fondo animado */}
      <div className="absolute inset-0 -z-10 bg-gradient-to-b from-[#EEF2FF] via-surface to-white" />
      <motion.div
        aria-hidden
        className="absolute -top-40 -right-32 w-[520px] h-[520px] rounded-full bg-primary-500/15 blur-3xl -z-10"
        animate={{ x: [0, 30, 0], y: [0, 20, 0] }}
        transition={{ duration: 14, repeat: Infinity, ease: "easeInOut" }}
      />
      <motion.div
        aria-hidden
        className="absolute top-40 -left-40 w-[460px] h-[460px] rounded-full bg-lilac-200/40 blur-3xl -z-10"
        animate={{ x: [0, -20, 0], y: [0, 30, 0] }}
        transition={{ duration: 16, repeat: Infinity, ease: "easeInOut" }}
      />
      <div aria-hidden className="absolute inset-0 -z-10 opacity-[0.35] [background-image:radial-gradient(#c7d2fe_1px,transparent_1px)] [background-size:26px_26px] [mask-image:radial-gradient(ellipse_at_center,black_30%,transparent_75%)]" />

      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 grid grid-cols-1 lg:grid-cols-[minmax(0,1.05fr)_minmax(0,1fr)] gap-14 items-center">
        <motion.div variants={contenedor} initial="hidden" animate="show" className="min-w-0">
          <motion.span variants={item} className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-white/80 backdrop-blur border border-blue-100 text-primary-600 text-xs font-semibold shadow-sm">
            <Sparkles className="w-3.5 h-3.5" /> La plataforma #1 para administradoras de conjuntos
          </motion.span>
          <motion.h1 variants={item} className="mt-6 text-[2.35rem] sm:text-5xl lg:text-[3.6rem] font-extrabold tracking-tight text-dark-100 leading-[1.08]">
            Administra tus propiedades de forma{" "}
            <span className="bg-gradient-to-r from-primary-500 to-primary-700 bg-clip-text text-transparent">inteligente y centralizada</span>
          </motion.h1>
          <motion.p variants={item} className="mt-6 text-lg text-gray-500 max-w-xl leading-relaxed">
            Gestiona residentes, propiedades, pagos, mantenimientos y documentos en un solo lugar.
            Con un asistente virtual que responde con datos reales.
          </motion.p>
          <motion.div variants={item} className="mt-8 flex flex-wrap gap-3">
            <Link to="/register">
              <Button variante="primary" tamano="lg" className="shadow-pill px-8">
                Empezar ahora <ArrowRight className="w-4 h-4" />
              </Button>
            </Link>
            <a href="#dashboard">
              <Button variante="outline" tamano="lg" className="bg-white/70 backdrop-blur">
                <PlayCircle className="w-4 h-4" /> Ver demo
              </Button>
            </a>
          </motion.div>
          <motion.ul variants={item} className="mt-6 flex flex-wrap gap-x-5 gap-y-2 text-sm text-gray-500">
            {["Usado por administradoras en Colombia", "Datos seguros", "Chatbot incluido"].map((t) => (
              <li key={t} className="flex items-center gap-1.5"><CheckCircle2 className="w-4 h-4 text-primary-500" /> {t}</li>
            ))}
          </motion.ul>
        </motion.div>

        {/* Mockup con perspectiva */}
        <motion.div
          initial={{ opacity: 0, scale: 0.92 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 1, delay: 0.3, ease: [0.22, 1, 0.36, 1] }}
          className="relative min-w-0 mt-6 lg:mt-0 lg:-mr-6 px-2 sm:px-6 lg:px-0"
        >
         <motion.div
          initial={{ rotateY: 0, rotateX: 0 }}
          animate={esEscritorio ? { rotateY: -6, rotateX: 3 } : { rotateY: 0, rotateX: 0 }}
          transition={{ duration: 1, delay: 0.3 }}
          style={{ transformPerspective: 1400 }}
         >
          <DashboardMock />
         </motion.div>

          <motion.div {...flotante(1.0)} className="absolute -top-5 right-0 sm:-right-6 bg-white rounded-2xl shadow-card-hover ring-1 ring-black/5 px-4 py-3 flex items-center gap-3">
            <span className="w-9 h-9 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center"><Wallet className="w-5 h-5" /></span>
            <div><p className="text-xs font-bold text-dark-100">Pago recibido</p><p className="text-[11px] text-gray-400">Apto 402 · $380.000</p></div>
          </motion.div>
          <motion.div {...flotante(1.3)} className="absolute -bottom-6 left-0 sm:-left-8 bg-white rounded-2xl shadow-card-hover ring-1 ring-black/5 px-4 py-3 flex items-center gap-3 max-w-[260px]">
            <span className="w-9 h-9 rounded-xl bg-primary-500 text-white flex items-center justify-center shrink-0"><Bot className="w-5 h-5" /></span>
            <div><p className="text-xs font-bold text-dark-100">Asistente virtual</p><p className="text-[11px] text-gray-400">“Tienes 3 mantenimientos urgentes hoy.”</p></div>
          </motion.div>
          <motion.div {...flotante(1.6)} className="hidden sm:flex absolute top-1/2 -right-10 bg-white rounded-2xl shadow-card-hover ring-1 ring-black/5 px-3 py-2 items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-primary-500" /><p className="text-[11px] font-semibold text-dark-100">Roles y permisos</p>
          </motion.div>
        </motion.div>
      </div>

      <motion.a
        href="#stats"
        aria-label="Bajar"
        className="absolute bottom-6 left-1/2 -translate-x-1/2 text-gray-400 hidden lg:block"
        animate={{ y: [0, 8, 0] }}
        transition={{ duration: 1.8, repeat: Infinity }}
      >
        <ChevronDown className="w-6 h-6" />
      </motion.a>
    </section>
  );
}
