import type { Usuario } from "@/types";

/**
 * Utilidades de RBAC en el frontend.
 *
 * Los permisos llegan desde el backend en `usuario.permisos` (lista de códigos
 * tipo "usuarios.ver", "finanzas.crear", ...), extraídos de la tabla
 * `rol_permisos` de PostgreSQL. Aquí se consultan para decidir qué mostrar
 * en el menú y qué rutas se pueden visitar.
 */

export const ROL_SUPER_ADMIN = 1;
export const ROL_ADMIN = 2;
export const ROL_RESIDENTE = 3;
export const ROL_TESORERIA = 4;
export const ROL_SEGURIDAD = 5;

/** Catálogo de roles asignables desde la UI (id → etiqueta). */
export const ROLES_UI: { id: number; label: string }[] = [
  { id: ROL_SUPER_ADMIN, label: "Super administrador" },
  { id: ROL_ADMIN, label: "Administrador" },
  { id: ROL_RESIDENTE, label: "Residente" },
  { id: ROL_TESORERIA, label: "Tesorería" },
  { id: ROL_SEGURIDAD, label: "Seguridad" },
];

/**
 * ¿El usuario tiene un permiso concreto por código? (ej. "finanzas.ver").
 * La ÚNICA fuente de verdad es la lista `usuario.permisos` que entrega el
 * backend (tabla rol_permisos). No hay atajos por rol_id: si el backend
 * quita un permiso a un rol, la UI lo refleja de inmediato.
 */
export function tienePermiso(usuario: Usuario | null, codigo: string): boolean {
  if (!usuario || !Array.isArray(usuario.permisos)) return false;
  return usuario.permisos.includes(codigo);
}

/** ¿Tiene al menos uno de los permisos indicados? */
export function tieneAlguno(usuario: Usuario | null, ...codigos: string[]): boolean {
  return codigos.some((c) => tienePermiso(usuario, c));
}

/** ¿El rol es de administración (super_admin o admin)? Solo para textos/UI, no autoriza nada. */
export function rolEsAdmin(usuario: Usuario | null): boolean {
  if (!usuario) return false;
  return usuario.rol_id === ROL_SUPER_ADMIN || usuario.rol_id === ROL_ADMIN;
}

/** ¿Es super administrador? */
export function esSuperAdmin(usuario: Usuario | null): boolean {
  return usuario?.rol_id === ROL_SUPER_ADMIN;
}

/**
 * Roles que el usuario actual puede asignar al crear/editar otros usuarios:
 * super_admin → todos; el resto (con usuarios.crear/editar) → todos menos super_admin.
 */
export function rolesAsignables(usuario: Usuario | null) {
  return esSuperAdmin(usuario) ? ROLES_UI : ROLES_UI.filter((r) => r.id !== ROL_SUPER_ADMIN);
}

/**
 * ¿Puede el usuario ver un módulo completo? Un módulo se considera
 * accesible si su rol tiene el permiso `<modulo>.ver`.
 */
export function puedeVerModulo(usuario: Usuario | null, modulo: string): boolean {
  return tienePermiso(usuario, `${modulo}.ver`);
}
