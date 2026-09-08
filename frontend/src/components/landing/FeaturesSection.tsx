import { motion } from "framer-motion";
import { BarChart3, Bot, Building2, FolderKanban, Wallet, Wrench } from "lucide-react";
import Container from "@/components/ui/Container";
import { contenedor, item, vista } from "./motion";

const features = [
  { icon: Building2, titulo: "Gestión de Residentes y Propiedades", desc: "Registra torres, apartamentos, propietarios y arrendatarios. Toda la información del conjunto ordenada y a un clic." },
  { icon: Wallet, titulo: "Finanzas y Pagos centralizados", desc: "Resumen de cartera, movimientos, conceptos de pago y reportes automáticos para la asamblea." },
  { icon: Wrench, titulo: "Órdenes de Mantenimiento", desc: "Los residentes reportan; tú priorizas, asignas y haces seguimiento por estado hasta el cierre." },
  { icon: FolderKanban, titulo: "Documentos y Eventos", desc: "Actas, reglamentos y circulares en un solo repositorio. Calendario de asambleas y reservas." },
  { icon: BarChart3, titulo: "Dashboard en tiempo real", desc: "Indicadores actualizados al instante: recaudo, morosidad, mantenimientos y ocupación." },
  { icon: Bot, titulo: "Asistente Virtual Inteligente", desc: "Pregunta en lenguaje natural y responde con datos reales de tu base de datos (RAG)." },
];

export default function FeaturesSection() {
  return (
    <section id="caracteristicas" className="py-24 bg-surface">
      <Container>
        <motion.div variants={contenedor} initial="hidden" whileInView="show" viewport={vista} className="text-center max-w-2xl mx-auto">
          <motion.span variants={item} className="text-xs font-bold tracking-widest text-primary-600 uppercase">Características</motion.span>
          <motion.h2 variants={item} className="mt-3 text-3xl sm:text-4xl font-extrabold tracking-tight text-dark-100">
            Todo lo que necesitas para administrar con excelencia
          </motion.h2>
          <motion.p variants={item} className="mt-4 text-gray-500">
            Módulos conectados entre sí, con permisos por rol y un asistente que conoce tu conjunto.
          </motion.p>
        </motion.div>

        <motion.div variants={contenedor} initial="hidden" whileInView="show" viewport={vista} className="mt-14 grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {features.map(({ icon: Icon, titulo, desc }) => (
            <motion.article
              key={titulo}
              variants={item}
              whileHover={{ y: -6, scale: 1.02 }}
              transition={{ type: "spring", stiffness: 300, damping: 22 }}
              className="group rounded-3xl bg-white p-7 shadow-card ring-1 ring-gray-100 hover:ring-primary-200 hover:shadow-card-hover transition-shadow"
            >
              <span className="w-12 h-12 rounded-2xl bg-primary-50 text-primary-600 flex items-center justify-center group-hover:bg-primary-500 group-hover:text-white transition-colors">
                <Icon className="w-6 h-6" />
              </span>
              <h3 className="mt-5 text-lg font-bold text-dark-100">{titulo}</h3>
              <p className="mt-2 text-sm text-gray-500 leading-relaxed">{desc}</p>
            </motion.article>
          ))}
        </motion.div>
      </Container>
    </section>
  );
}
