// --- Tipos de dominio del sistema (coinciden con los schemas del backend) ---

export interface Usuario {
  id: number;
  nombre: string;
  telefono?: string;
  correo: string;
  rol_id: number;
  nombre_rol?: string;
  activo: boolean;
  id_copropiedad?: number;
  /** Lista de códigos de permiso (RBAC) asignados al rol del usuario. */
  permisos?: string[];
}

export interface Residente {
  id: number;
  usuario_id?: number;
  tipo: string;
  identificacion: string;
  telefono_adicional?: string;
  contacto_emergencia?: string;
  telefono_emergencia?: string;
  activo: boolean;
  nombre?: string;
}

export interface Propiedad {
  id: number;
  residencial: string;
  bloque?: string;
  torre?: string;
  apartamento: string;
  piso?: number;
  area?: number;
  habitaciones: number;
  banos: number;
  parqueaderos: number;
  estado: string;
  estrato?: number;
  residente_id?: number;
  residente_nombre?: string;
}

export interface Concepto {
  id: number;
  codigo: string;
  nombre: string;
  tipo: string;
  monto_default?: number;
  recurrente: boolean;
  descripcion?: string;
}

export interface Movimiento {
  id: number;
  propiedad_id?: number;
  propiedad_desc?: string;
  concepto_id: number;
  concepto_nombre: string;
  monto: number;
  fecha_vencimiento: string;
  fecha_pago?: string;
  estado: string;
  numero_recibo?: string;
  metodo_pago?: string;
  referencia?: string;
  notas?: string;
  fecha_creacion: string;
}

export interface TareaMantenimiento {
  id: number;
  propiedad_id?: number;
  residente_id?: number;
  titulo: string;
  descripcion: string;
  prioridad: string;
  estado: string;
  asignado_a?: number;
  costo_estimado?: number;
  fecha_programada?: string;
  fecha_completada?: string;
  fecha_creacion: string;
  propiedad_desc?: string;
}

export interface Documento {
  id: number;
  titulo: string;
  descripcion?: string;
  ruta_archivo: string;
  tipo_documento?: string;
  mime?: string;
  tamano?: number;
  propiedad_id?: number;
  subido_por?: number;
  publico: boolean;
  version: number;
  fecha_creacion: string;
}

export interface Evento {
  id: number;
  titulo: string;
  descripcion?: string;
  fecha: string;
  lugar?: string;
  creado_por?: number;
}

export interface DashboardStats {
  usuarios: number;
  residentes: number;
  propiedades: number;
  pagos_pendientes: number;
  pagos_pagados: number;
  ingresos: number;
  gastos: number;
  saldo: number;
  mantenimientos_pendientes: number;
  mantenimientos_completados: number;
  documentos: number;
}

export interface Notificacion {
  tipo: "mora" | "proximo" | "evento" | "mantenimiento";
  severidad: "alta" | "media" | "baja";
  titulo: string;
  mensaje: string;
  fecha: string | null;
}

export interface ChatRespuesta {
  sesion_id: number;
  respuesta: string;
  mensaje?: unknown;
}

export interface ChatMensaje {
  id: number;
  sesion_id: number;
  rol: string;
  contenido: string;
  fecha_creacion: string;
}
