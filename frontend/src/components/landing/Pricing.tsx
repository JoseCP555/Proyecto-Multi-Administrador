import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { Check } from "lucide-react";
import Button from "@/components/ui/Button";
import Container from "@/components/ui/Container";
import { contenedor, item, vista } from "./motion";

const planes = [
  { nombre: "Inicial", precio: "Gratis", detalle: "Para un conjunto pequeño", destacado: false, items: ["Hasta 50 unidades", "Residentes y propiedades", "Mantenimientos y eventos", "Chatbot básico"] },
  { nombre: "Profesional", precio: "$149.000", detalle: "COP / mes por conjunto", destacado: true, items: ["Unidades ilimitadas", "Finanzas y reportes", "Roles y permisos avanzados", "Chatbot con datos reales", "Soporte prioritario"] },
  { nombre: "Administradora", precio: "A medida", detalle: "Varios conjuntos", destacado: false, items: ["Múltiples copropiedades", "Usuarios ilimitados", "Respaldo y auditoría", "Acompañamiento dedicado"] },
];

export default function Pricing() {
  return (
    <section id="planes" className="py-24 bg-white">
      <Container>
        <motion.div variants={contenedor} initial="hidden" whileInView="show" viewport={vista} className="text-center max-w-2xl mx-auto">
          <motion.span variants={item} className="text-xs font-bold tracking-widest text-primary-600 uppercase">Planes</motion.span>
          <motion.h2 variants={item} className="mt-3 text-3xl sm:text-4xl font-extrabold tracking-tight text-dark-100">Planes para administradoras</motion.h2>
          <motion.p variants={item} className="mt-4 text-gray-500">Empieza gratis y crece cuando lo necesites.</motion.p>
        </motion.div>

        <motion.div variants={contenedor} initial="hidden" whileInView="show" viewport={vista} className="mt-14 grid gap-6 lg:grid-cols-3 items-stretch">
          {planes.map((p) => (
            <motion.div key={p.nombre} variants={item} whileHover={{ y: -6 }} transition={{ type: "spring", stiffness: 260, damping: 20 }}
              className={`relative rounded-3xl p-8 flex flex-col ${p.destacado ? "bg-dark-100 text-white shadow-shell" : "bg-white ring-1 ring-gray-100 shadow-card"}`}>
              {p.destacado && <span className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-1 rounded-full bg-primary-500 text-white text-[11px] font-bold">Más popular</span>}
              <p className={`text-sm font-semibold ${p.destacado ? "text-blue-200" : "text-gray-500"}`}>{p.nombre}</p>
              <p className="mt-3 text-4xl font-extrabold tracking-tight">{p.precio}</p>
              <p className={`text-xs mt-1 ${p.destacado ? "text-blue-200" : "text-gray-400"}`}>{p.detalle}</p>
              <ul className="mt-7 space-y-3 text-sm flex-1">
                {p.items.map((x) => (
                  <li key={x} className="flex items-start gap-2.5">
                    <span className={`mt-0.5 w-5 h-5 rounded-full flex items-center justify-center shrink-0 ${p.destacado ? "bg-primary-500" : "bg-primary-50 text-primary-600"}`}><Check className="w-3 h-3" /></span>
                    <span className={p.destacado ? "text-blue-50" : "text-gray-600"}>{x}</span>
                  </li>
                ))}
              </ul>
              <Link to="/register" className="mt-8">
                <Button variante={p.destacado ? "primary" : "outline"} tamano="lg" className={`w-full ${p.destacado ? "shadow-pill" : ""}`}>
                  {p.precio === "A medida" ? "Hablar con ventas" : "Empezar"}
                </Button>
              </Link>
            </motion.div>
          ))}
        </motion.div>
      </Container>
    </section>
  );
}
