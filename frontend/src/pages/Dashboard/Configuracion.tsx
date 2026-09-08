import { useState, type FormEvent } from "react";
import { Save, DatabaseBackup, Loader2 } from "lucide-react";
import Card from "@/components/ui/Card";
import Button from "@/components/ui/Button";
import { useFetch } from "@/hooks/useFetch";
import { usePermisos } from "@/lib/usePermisos";
import { api } from "@/lib/api";
import { descargarArchivo } from "@/lib/download";

interface ConfItem {
  id: number;
  clave: string;
  valor: string;
  descripcion?: string;
}

const BASE = import.meta.env.VITE_API_URL || "/api";

// Configuración global + respaldo de base de datos (solo administradores).
export default function Configuracion() {
  const { puede } = usePermisos();
  const { data, setData, cargar, cargando } = useFetch<ConfItem[]>("/configuracion");
  const [editando, setEditando] = useState<Record<string, string>>({});
  const [guardando, setGuardando] = useState(false);
  const [msg, setMsg] = useState("");
  const [respaldando, setRespaldando] = useState(false);

  const puedeEditar = puede("config.editar");

  const guardar = async (e: FormEvent) => {
    e.preventDefault();
    setGuardando(true);
    setMsg("");
    try {
      const items = (data ?? []).map((c) => ({
        clave: c.clave,
        valor: editando[c.clave] !== undefined ? editando[c.clave] : c.valor,
        descripcion: c.descripcion ?? "",
      }));
      const res = await api.put<ConfItem[]>("/configuracion", items);
      setData(res);
      setEditando({});
      setMsg("Configuración guardada correctamente.");
    } catch (err) {
      setMsg(`Error: ${(err as Error).message}`);
    } finally {
      setGuardando(false);
    }
  };

  const respaldar = async () => {
    setRespaldando(true);
    setMsg("");
    try {
      await descargarArchivo(`${BASE}/admin/backup`, "multiadmin_db_backup.sql");
      setMsg("Respaldo de base de datos descargado.");
    } catch (err) {
      setMsg(`Error al generar el respaldo: ${(err as Error).message}`);
    } finally {
      setRespaldando(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-bold text-gray-900">Configuración del sistema</h2>
          <p className="text-sm text-gray-500">Parámetros globales de la copropiedad.</p>
        </div>
        {puede("sistema.respaldar") && (
          <Button variante="outline" tamano="sm" onClick={respaldar} disabled={respaldando}>
            {respaldando ? <Loader2 className="w-4 h-4 animate-spin" /> : <DatabaseBackup className="w-4 h-4" />}
            Respaldar BD
          </Button>
        )}
      </div>

      {msg && <div className="text-sm text-primary-700 bg-blue-50 border border-blue-200 rounded-lg px-4 py-3">{msg}</div>}

      <Card>
        {cargando && <p className="text-sm text-gray-400 py-6 text-center">Cargando...</p>}
        <form onSubmit={guardar} className="space-y-4">
          {(data ?? []).map((c) => (
            <div key={c.clave}>
              <label className="label">{c.descripcion || c.clave}</label>
              <input
                className="input"
                value={editando[c.clave] !== undefined ? editando[c.clave] : c.valor}
                onChange={(e) => setEditando((s) => ({ ...s, [c.clave]: e.target.value }))}
                disabled={!puedeEditar}
              />
            </div>
          ))}
          {puedeEditar && (
            <Button variante="primary" type="submit" disabled={guardando}>
              <Save className="w-4 h-4" /> {guardando ? "Guardando..." : "Guardar cambios"}
            </Button>
          )}
        </form>
      </Card>
    </div>
  );
}
