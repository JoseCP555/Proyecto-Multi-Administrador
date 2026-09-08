import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { AnimatePresence, motion, useInView } from "framer-motion";
import { useRef } from "react";
import { ArrowRight, Bot, User } from "lucide-react";
import Button from "@/components/ui/Button";
import Container from "@/components/ui/Container";
import { contenedor, item, vista } from "./motion";
import logoUrl from "@/lib/logo";

const guion = [
  { de: "user", texto: "¿Cuántos pagos pendientes hay este mes?" },
  { de: "bot", texto: "Hay 12 pagos pendientes por $4.560.000. Los más atrasados: Apto 302 (3 meses) y Casa 15 (2 meses)." },
  { de: "user", texto: "¿Y mantenimientos abiertos en Torre B?" },
  { de: "bot", texto: "3 órdenes abiertas: ascensor (alta), luminarias parqueadero (media) y filtración piso 4 (alta). ¿Quieres asignar alguna?" },
] as const;

export default function ChatbotSection() {
  const ref = useRef<HTMLDivElement>(null);
  const visible = useInView(ref, { once: true, margin: "-120px" });
  const [n, setN] = useState(0);
  const [escribiendo, setEscribiendo] = useState(false);

  useEffect(() => {
    if (!visible || n >= guion.length) return;
    const esBot = guion[n].de === "bot";
    setEscribiendo(esBot);
    const t = setTimeout(() => { setEscribiendo(false); setN((v) => v + 1); }, esBot ? 1400 : 800);
    return () => clearTimeout(t);
  }, [visible, n]);

  return (
    <section id="chatbot" className="relative py-24 overflow-hidden bg-gradient-to-br from-[#0B1B4D] via-primary-700 to-primary-600 text-white">
      <div aria-hidden className="absolute -top-32 -left-20 w-[420px] h-[420px] rounded-full bg-white/10 blur-3xl" />
      <div aria-hidden className="absolute -bottom-40 -right-20 w-[520px] h-[520px] rounded-full bg-primary-500/40 blur-3xl" />
      <Container className="relative grid lg:grid-cols-2 gap-14 items-center">
        <motion.div variants={contenedor} initial="hidden" whileInView="show" viewport={vista}>
          <motion.span variants={item} className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-white/10 ring-1 ring-white/20 text-xs font-semibold">
            <Bot className="w-3.5 h-3.5" /> Asistente virtual
          </motion.span>
          <motion.h2 variants={item} className="mt-5 text-3xl sm:text-4xl font-extrabold tracking-tight leading-tight">
            Tu asistente virtual que conoce tu conjunto
          </motion.h2>
          <motion.p variants={item} className="mt-5 text-blue-100 text-lg leading-relaxed">
            Pregúntale sobre pagos pendientes, órdenes de mantenimiento, residentes o documentos.
            Responde con información real de la base de datos, respetando los permisos de cada rol.
          </motion.p>
          <motion.div variants={item} className="mt-8">
            <Link to="/register">
              <Button variante="outline" tamano="lg" className="bg-white text-primary-700 border-white hover:bg-blue-50">
                Probar el chatbot <ArrowRight className="w-4 h-4" />
              </Button>
            </Link>
          </motion.div>
        </motion.div>

        <motion.div ref={ref} initial={{ opacity: 0, y: 40 }} whileInView={{ opacity: 1, y: 0 }} viewport={vista} transition={{ duration: 0.7 }}
          className="rounded-[28px] bg-white/10 backdrop-blur-xl ring-1 ring-white/20 p-4 sm:p-6 shadow-2xl">
          <div className="flex items-center gap-3 pb-4 border-b border-white/10">
            <span className="w-10 h-10 rounded-full bg-white flex items-center justify-center"><img src={logoUrl} alt="" className="w-8 h-8" /></span>
            <div><p className="text-sm font-bold">Asistente Multi.Admin</p><p className="text-[11px] text-blue-200 flex items-center gap-1"><span className="w-1.5 h-1.5 rounded-full bg-emerald-400" /> En línea · datos en tiempo real</p></div>
          </div>
          <div className="mt-4 space-y-3 min-h-[260px]">
            <AnimatePresence>
              {guion.slice(0, n).map((m, i) => (
                <motion.div key={i} initial={{ opacity: 0, y: 12, scale: 0.97 }} animate={{ opacity: 1, y: 0, scale: 1 }} transition={{ duration: 0.35 }}
                  className={`flex items-end gap-2 ${m.de === "user" ? "justify-end" : ""}`}>
                  {m.de === "bot" && <span className="w-7 h-7 rounded-full bg-white/20 flex items-center justify-center shrink-0"><Bot className="w-4 h-4" /></span>}
                  <p className={`max-w-[80%] text-sm leading-relaxed px-4 py-2.5 rounded-2xl ${m.de === "user" ? "bg-white text-dark-100 rounded-br-md" : "bg-white/15 ring-1 ring-white/10 rounded-bl-md"}`}>{m.texto}</p>
                  {m.de === "user" && <span className="w-7 h-7 rounded-full bg-white/20 flex items-center justify-center shrink-0"><User className="w-4 h-4" /></span>}
                </motion.div>
              ))}
              {escribiendo && (
                <motion.div key="typing" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="flex items-end gap-2">
                  <span className="w-7 h-7 rounded-full bg-white/20 flex items-center justify-center"><Bot className="w-4 h-4" /></span>
                  <span className="px-4 py-3 rounded-2xl rounded-bl-md bg-white/15 flex gap-1">
                    {[0, 1, 2].map((k) => <motion.span key={k} className="w-1.5 h-1.5 rounded-full bg-white/80" animate={{ y: [0, -4, 0] }} transition={{ duration: 0.8, repeat: Infinity, delay: k * 0.15 }} />)}
                  </span>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
          <div className="mt-4 h-11 rounded-full bg-white/10 ring-1 ring-white/15 flex items-center px-4 text-sm text-blue-200">Escribe tu pregunta…</div>
        </motion.div>
      </Container>
    </section>
  );
}
