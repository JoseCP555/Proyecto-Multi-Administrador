import { useAuth } from "@/context/AuthContext";
import { tienePermiso, tieneAlguno, rolEsAdmin, esSuperAdmin } from "@/lib/permisos";

/**
 * Hook de RBAC para componentes: expone helpers para saber si el usuario
 * autenticado puede ejecutar una acción por código de permiso.
 *
 * Ejemplo:
 *   const { puede, esAdmin } = usePermisos();
 *   if (puede("finanzas.crear")) mostrarBotonNuevo();
 */
export function usePermisos() {
  const { usuario } = useAuth();
  return {
    usuario,
    /** ¿Tiene el permiso `<codigo>`? (ej. "usuarios.eliminar") */
    puede: (codigo: string) => tienePermiso(usuario, codigo),
    /** ¿Tiene alguno de los permisos? */
    puedeAlguno: (...codigos: string[]) => tieneAlguno(usuario, ...codigos),
    /** ¿El rol es de administración (super_admin/admin)? Solo informativo. */
    esAdmin: () => rolEsAdmin(usuario),
    /** ¿Es super administrador? */
    esSuper: () => esSuperAdmin(usuario),
  };
}
