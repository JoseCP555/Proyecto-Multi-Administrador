import { motion } from "framer-motion";
import { Crown, ShieldCheck, UserRound, Wallet, Eye } from "lucide-react";
import Container from "@/components/ui/Container";
import { useScrollAnimation } from "@/hooks/useScrollAnimation";
import { staggerContainer, childrenItem } from "@/utils/animations";

// Roles del sistema y qué puede hacer cada uno (RBAC).
const roles = [
  {
    nombre: "Super Admin / Admin",
    icon: Crown,
    color: "text-purple-600 bg-purple-50",
    border: "border-purple-200",
    permisos: [
      "Acceso total a todos los módulos",
      "Gestión de usuarios, roles y permisos",
      "Configuración del conjunto",
      "Eliminar y editar cualquier registro",
    ],
  },
  {
    nombre: "Tesorería",
    icon: Wallet,
    color: "text-amber-600 bg-amber-50",
    border: "border-amber-200",
    permisos: [
      "Finanzas: ingresos, gastos y mora",
      "Reportes y dashboard financiero",
      "Documentos (ver y descargar)",
      "Chat asistente",
    ],
  },
  {
    nombre: "Residente",
    icon: UserRound,
    color: "text-emerald-600 bg-emerald-50",
    border: "border-emerald-200",
    permisos: [
      "Ver sus propiedades y documentos",
      "Reportar mantenimientos",
      "Consultar eventos del conjunto",
      "Chat asistente",
    ],
  },
  {
    nombre: "Seguridad",
    icon: ShieldCheck,
    color: "text-gray-600 bg-gray-50",
    border: "border-gray-200",
    permisos: [
      "Consulta de residentes y propiedades",
      "Estado de mantenimientos",
      "Eventos y novedades",
      "Chat asistente",
    ],
  },
];

export default function RolesSection() {
  const { ref, controls } = useScrollAnimation();

  return (
    <section id="roles" className="py-20 bg-surface">
      <Container>
        <motion.div ref={ref} initial="initial" animate={controls} variants={staggerContainer}>
          <motion.div variants={childrenItem} className="text-center max-w-2xl mx-auto mb-14">
            <span className="text-primary-600 text-sm font-semibold uppercase tracking-wider">
              Roles y permisos
            </span>
            <h2 className="text-3xl sm:text-4xl font-bold text-dark-100 mt-2">
              Cada usuario con su nivel de acceso
            </h2>
            <p className="mt-4 text-gray-500 text-lg">
              El sistema aplica controles de acceso por rol: cada quien ve y hace solo lo que le
              corresponde. Seguridad desde la base de datos.
            </p>
          </motion.div>

          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {roles.map((r) => (
              <motion.div
                key={r.nombre}
                variants={childrenItem}
                whileHover={{ y: -8, transition: { duration: 0.2 } }}
                className={`bg-white rounded-xl border ${r.border} shadow-sm p-6 hover:shadow-card-hover transition-all duration-200`}
              >
                <div className={`w-12 h-12 rounded-lg flex items-center justify-center mb-4 ${r.color}`}>
                  <r.icon className="w-6 h-6" />
                </div>
                <h3 className="text-base font-semibold text-gray-800">{r.nombre}</h3>
                <ul className="mt-3 space-y-2">
                  {r.permisos.map((p) => (
                    <li key={p} className="flex items-start gap-2 text-sm text-gray-500">
                      <Eye className="w-4 h-4 mt-0.5 shrink-0 text-primary-500" />
                      {p}
                    </li>
                  ))}
                </ul>
              </motion.div>
            ))}
          </div>
        </motion.div>
      </Container>
    </section>
  );
}
