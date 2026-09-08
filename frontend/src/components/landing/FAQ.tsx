import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronDown } from "lucide-react";
import Container from "@/components/ui/Container";
import { useScrollAnimation } from "@/hooks/useScrollAnimation";

// Preguntas frecuentes con respuesta desplegable.
const preguntas = [
  {
    q: "¿Qué es Multi-Administrador?",
    a: "Es un sistema web integral para la administración de conjuntos residenciales: gestiona residentes, propiedades, finanzas, mantenimientos, documentos, eventos y reportes desde un solo lugar.",
  },
  {
    q: "¿Necesito conocimientos técnicos para usarlo?",
    a: "No. Su interfaz es intuitiva y funciona como cualquier dashboard web. En pocos clics registras pagos, residentes, propiedades y generas reportes sin hojas de cálculo.",
  },
  {
    q: "¿Cómo se protegen los datos de mi conjunto?",
    a: "Cada usuario ingresa con un rol y permisos definidos en la base de datos (RBAC). Además, las contraseñas se almacenan cifradas y las sesiones usan tokens seguros que pueden revocarse.",
  },
  {
    q: "¿Puedo controlar qué ve cada residente?",
    a: "Sí. Los residentes ven su información, propiedades, documentos y eventos, y pueden reportar mantenimientos. Las áreas financieras y de administración quedan reservadas a los roles autorizados.",
  },
  {
    q: "¿Incluye asistente inteligente?",
    a: "Sí, tiene un chatbot integrado que responde con los datos reales de tu conjunto: saldo, pagos pendientes, mantenimientos, propiedades, documentos y próximos eventos.",
  },
  {
    q: "¿La recuperación de contraseña funciona?",
    a: "Sí. Recibes por correo un código de 6 dígitos y un enlace; ambos expiran en 30 minutos. Al registrarte también verificas tu correo con un código.",
  },
];

export default function FAQ() {
  const { ref, controls } = useScrollAnimation();
  const [abierta, setAbierta] = useState<number | null>(0);

  return (
    <section id="faq" className="py-20 bg-white">
      <Container>
        <motion.div ref={ref} initial="initial" animate={controls}>
          <div className="text-center max-w-2xl mx-auto mb-14">
            <span className="text-primary-600 text-sm font-semibold uppercase tracking-wider">
              Preguntas frecuentes
            </span>
            <h2 className="text-3xl sm:text-4xl font-bold text-dark-100 mt-2">
              Resolvemos tus dudas
            </h2>
            <p className="mt-4 text-gray-500 text-lg">
              Lo que más preguntan los administradores y residentes.
            </p>
          </div>

          <div className="max-w-3xl mx-auto space-y-3">
            {preguntas.map((item, i) => {
              const activa = abierta === i;
              return (
                <div
                  key={item.q}
                  className="rounded-xl border border-gray-200 bg-surface overflow-hidden"
                >
                  <button
                    onClick={() => setAbierta(activa ? null : i)}
                    className="w-full flex items-center justify-between gap-4 px-5 py-4 text-left"
                  >
                    <span className="font-medium text-gray-800 text-sm sm:text-base">{item.q}</span>
                    <ChevronDown
                      className={`w-5 h-5 text-gray-400 shrink-0 transition-transform ${
                        activa ? "rotate-180 text-primary-500" : ""
                      }`}
                    />
                  </button>
                  <AnimatePresence initial={false}>
                    {activa && (
                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: "auto", opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.2 }}
                      >
                        <p className="px-5 pb-5 text-sm text-gray-500 leading-relaxed">{item.a}</p>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              );
            })}
          </div>
        </motion.div>
      </Container>
    </section>
  );
}
