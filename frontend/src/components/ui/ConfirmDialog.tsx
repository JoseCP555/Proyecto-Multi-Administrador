import { motion, AnimatePresence } from "framer-motion";
import { Trash2, AlertTriangle } from "lucide-react";
import Button from "./Button";

// Diálogo de confirmación para acciones destructivas (eliminar).
export default function ConfirmDialog({
  abierto,
  titulo = "¿Estás seguro?",
  mensaje,
  onCancelar,
  onConfirmar,
  cargando = false,
}: {
  abierto: boolean;
  titulo?: string;
  mensaje: string;
  onCancelar: () => void;
  onConfirmar: () => void;
  cargando?: boolean;
}) {
  return (
    <AnimatePresence>
      {abierto && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="absolute inset-0 bg-black/40" onClick={onCancelar} />
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className="relative bg-white rounded-2xl shadow-2xl w-full max-w-sm p-6 text-center"
          >
            <div className="w-14 h-14 mx-auto rounded-full bg-red-50 text-danger flex items-center justify-center mb-4">
              <AlertTriangle className="w-7 h-7" />
            </div>
            <h3 className="text-lg font-semibold text-gray-800">{titulo}</h3>
            <p className="text-sm text-gray-500 mt-2">{mensaje}</p>
            <div className="mt-6 grid grid-cols-2 gap-3">
              <Button variante="outline" onClick={onCancelar} disabled={cargando}>
                Cancelar
              </Button>
              <Button variante="danger" onClick={onConfirmar} disabled={cargando}>
                <Trash2 className="w-4 h-4" /> {cargando ? "Eliminando..." : "Eliminar"}
              </Button>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}
