import { Link } from "react-router-dom";
import { ShieldAlert } from "lucide-react";
import Badge from "@/components/ui/Badge";
import { useAuth } from "@/context/AuthContext";

/** Pantalla que se muestra cuando el rol del usuario no tiene el permiso requerido. */
export default function SinPermiso({ permiso }: { permiso?: string }) {
  const { usuario } = useAuth();
  return (
    <div className="card p-10 text-center max-w-xl mx-auto">
      <div className="mx-auto w-14 h-14 rounded-2xl bg-red-50 flex items-center justify-center mb-4">
        <ShieldAlert className="w-7 h-7 text-danger" />
      </div>
      <h2 className="text-xl font-bold text-dark-100">Acceso restringido</h2>
      <p className="text-gray-500 mt-2">
        Tu rol <Badge color="info">{usuario?.nombre_rol ?? "sin rol"}</Badge> no tiene
        permiso para ver esta sección
        {permiso && <> (<code className="text-xs bg-gray-100 px-1.5 py-0.5 rounded">{permiso}</code>)</>}.
      </p>
      <p className="text-sm text-gray-400 mt-1">Si crees que es un error, contacta a la administración.</p>
      <Link to="/dashboard" className="btn btn-primary inline-flex mt-6">Volver al inicio</Link>
    </div>
  );
}
