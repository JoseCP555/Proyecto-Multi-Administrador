import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { ArrowRight } from "lucide-react";
import Button from "@/components/ui/Button";
import Container from "@/components/ui/Container";
import { contenedor, item, vista } from "./motion";
import logoUrl from "@/lib/logo";

export default function CTASection() {
  return (
    <section className="py-24 bg-surface">
      <Container>
        <motion.div variants={contenedor} initial="hidden" whileInView="show" viewport={vista}
          className="relative overflow-hidden rounded-[32px] bg-dark-100 px-8 py-16 sm:py-20 text-center shadow-shell">
          <div aria-hidden className="absolute -top-24 -right-24 w-80 h-80 rounded-full bg-primary-500/40 blur-3xl" />
          <div aria-hidden className="absolute -bottom-24 -left-24 w-80 h-80 rounded-full bg-lilac-200/20 blur-3xl" />
          <img src={logoUrl} alt="" className="relative mx-auto w-16 h-16 rounded-full bg-white p-1 mb-6" />
          <motion.h2 variants={item} className="relative text-3xl sm:text-5xl font-extrabold tracking-tight text-white leading-tight">
            Empieza a administrar mejor tu conjunto hoy
          </motion.h2>
          <motion.p variants={item} className="relative mt-5 text-gray-300 text-lg max-w-2xl mx-auto">
            Centraliza residentes, pagos, mantenimientos y documentos, y deja que el asistente responda por ti.
          </motion.p>
          <motion.div variants={item} className="relative mt-9">
            <Link to="/register">
              <Button variante="primary" tamano="lg" className="px-9 shadow-pill">
                Crear cuenta gratis <ArrowRight className="w-4 h-4" />
              </Button>
            </Link>
            <p className="mt-4 text-xs text-gray-400">Sin tarjeta de crédito · Configuración en menos de 5 minutos</p>
          </motion.div>
        </motion.div>
      </Container>
    </section>
  );
}
