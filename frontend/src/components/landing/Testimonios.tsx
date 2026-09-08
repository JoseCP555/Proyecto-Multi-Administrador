import { useEffect, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Quote, Star } from "lucide-react";
import Container from "@/components/ui/Container";
import { contenedor, item, vista } from "./motion";

const testimonios = [
  { nombre: "Laura Gómez", cargo: "Administradora · Conjunto Las Palmas", ini: "LG", texto: "Pasé de tres hojas de cálculo y un grupo de WhatsApp a un solo panel. La cartera bajó 30% en cuatro meses porque ahora sí sé a quién cobrar." },
  { nombre: "Carlos Ruiz", cargo: "Consejo de administración · Torres del Parque", ini: "CR", texto: "El chatbot es lo que más usan los residentes: preguntan su saldo o el estado de un arreglo y reciben la respuesta al instante, sin llamar a portería." },
  { nombre: "Ana María Torres", cargo: "Gerente · Administradora Horizonte (18 conjuntos)", ini: "AT", texto: "Los roles y permisos nos dieron tranquilidad: cada contador, vigilante y residente ve exactamente lo que debe ver. Nada más." },
];

export default function Testimonios() {
  const [i, setI] = useState(0);
  useEffect(() => {
    const t = setInterval(() => setI((v) => (v + 1) % testimonios.length), 6000);
    return () => clearInterval(t);
  }, []);
  const t = testimonios[i];

  return (
    <section id="testimonios" className="py-24 bg-surface">
      <Container>
        <motion.div variants={contenedor} initial="hidden" whileInView="show" viewport={vista} className="text-center max-w-2xl mx-auto">
          <motion.span variants={item} className="text-xs font-bold tracking-widest text-primary-600 uppercase">Testimonios</motion.span>
          <motion.h2 variants={item} className="mt-3 text-3xl sm:text-4xl font-extrabold tracking-tight text-dark-100">Administradoras que ya confían</motion.h2>
        </motion.div>

        <div className="mt-12 grid gap-6 lg:grid-cols-3">
          {/* Desktop: grid; el activo se resalta. Mobile: carrusel */}
          {testimonios.map((x, k) => (
            <motion.figure
              key={x.nombre}
              variants={item} initial="hidden" whileInView="show" viewport={vista} transition={{ delay: k * 0.12 }}
              onMouseEnter={() => setI(k)}
              className={`hidden lg:flex flex-col rounded-3xl p-7 ring-1 transition-all duration-500 ${k === i ? "bg-white shadow-card-hover ring-primary-200 -translate-y-2" : "bg-white/70 ring-gray-100"}`}
            >
              <Quote className="w-6 h-6 text-primary-200" />
              <div className="mt-3 flex gap-0.5">{[...Array(5)].map((_, s) => <Star key={s} className="w-4 h-4 fill-warning text-warning" />)}</div>
              <blockquote className="mt-4 text-gray-600 leading-relaxed flex-1">“{x.texto}”</blockquote>
              <figcaption className="mt-6 flex items-center gap-3">
                <span className="w-11 h-11 rounded-full bg-gradient-to-br from-primary-500 to-primary-700 text-white text-sm font-bold flex items-center justify-center">{x.ini}</span>
                <div><p className="text-sm font-bold text-dark-100">{x.nombre}</p><p className="text-xs text-gray-400">{x.cargo}</p></div>
              </figcaption>
            </motion.figure>
          ))}

          <div className="lg:hidden">
            <AnimatePresence mode="wait">
              <motion.figure key={i} initial={{ opacity: 0, x: 30 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -30 }} transition={{ duration: 0.4 }}
                className="rounded-3xl bg-white p-7 shadow-card ring-1 ring-gray-100">
                <div className="flex gap-0.5">{[...Array(5)].map((_, s) => <Star key={s} className="w-4 h-4 fill-warning text-warning" />)}</div>
                <blockquote className="mt-4 text-gray-600 leading-relaxed">“{t.texto}”</blockquote>
                <figcaption className="mt-6 flex items-center gap-3">
                  <span className="w-11 h-11 rounded-full bg-gradient-to-br from-primary-500 to-primary-700 text-white text-sm font-bold flex items-center justify-center">{t.ini}</span>
                  <div><p className="text-sm font-bold text-dark-100">{t.nombre}</p><p className="text-xs text-gray-400">{t.cargo}</p></div>
                </figcaption>
              </motion.figure>
            </AnimatePresence>
            <div className="mt-5 flex justify-center gap-2">
              {testimonios.map((_, k) => (
                <button key={k} onClick={() => setI(k)} aria-label={`Testimonio ${k + 1}`} className={`h-2 rounded-full transition-all ${k === i ? "w-6 bg-primary-500" : "w-2 bg-gray-300"}`} />
              ))}
            </div>
          </div>
        </div>
      </Container>
    </section>
  );
}
