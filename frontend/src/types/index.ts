// --- Tipos de dominio del sistema (coinciden con los schemas del backend) ---

/** Conjunto / copropiedad gestionada por la plataforma (HU-07). */
export interface Conjunto {
  id: number;
  nombre: string;
  nit?: string;
  direccion?: string;
  ciudad?: string;
  telefono?: string;
  correo?: string;
  administrador?: string;
  habitantes: number;
  cuota: number;
  dia_cobro?: number;
  reunion?: string;
  silencio?: string;
  logo?: string;
  /** Id de paleta ("azul", ...) o hexadecimal #RRGGBB. null = automático. */
  color?: string | null;
  /** Umbral de gasto que dispara la alerta al consejo (UH-26). */
  umbral_gasto?: number | null;
  activo: boolean;
  fecha_creacion?: string;
  /** Métricas calculadas por el backend. */
  propiedades: number;
  residentes: number;
  saldo: number;
}

export interface Usuario {
  id: number;
  nombre: string;
  telefono?: string;
  correo: string;
  rol_id: number;
  nombre_rol?: string;
  activo: boolean;
  id_copropiedad?: number;
  /** Foto de perfil (data URI o URL) — UH-20. */
  foto?: string | null;
  correo_verificado?: boolean;
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
  correo?: string;
  rol_id?: number;
  nombre_rol?: string;
  apartamento?: string;
  propiedad_id?: number;
}

export interface CarteraUnidad {
  propiedad_id: number;
  apartamento: string;
  torre?: string | null;
  bloque?: string | null;
  residente_id?: number | null;
  residente_nombre?: string | null;
  facturado: number;
  pagado: number;
  pendiente: number;
  vencido: number;
  estado_pago: "al_dia" | "pendiente" | "en_mora" | string;
}

export interface CarteraResumen {
  periodo: string;
  desde?: string | null;
  hasta?: string | null;
  unidades: CarteraUnidad[];
  al_dia: number;
  con_saldo: number;
  total_facturado: number;
  total_pagado: number;
  total_pendiente: number;
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
  /** zona_comun | unidad | otro (UH-21) */
  categoria?: string;
  /** Nombres de archivo de las fotos adjuntas, separados por coma. */
  evidencias?: string | null;
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
  /** Hora del evento en formato HH:MM (UH-04). */
  hora?: string | null;
  /** asamblea | reunion | actividad | mantenimiento */
  tipo?: string | null;
  notificado_48h?: boolean;
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

/** Aviso persistente generado por un hecho real del sistema. */
export interface Notificacion {
  id: number;
  tipo: string;
  severidad: "alta" | "media" | "baja";
  titulo: string;
  mensaje: string;
  /** Fecha del hecho (YYYY-MM-DD), no de creación del aviso. */
  fecha: string | null;
  fecha_creacion?: string | null;
  leida?: boolean;
  url?: string | null;
  id_conjunto?: number | null;
  nombre_conjunto?: string | null;
}

export interface PreferenciasNotificacion {
  correo: boolean;
  push: boolean;
  correo_configurado: boolean;
  push_configurado: boolean;
  vapid_publico: string | null;
}

export interface ChatRespuesta {
  sesion_id: number;
  respuesta: string;
  motor_usado?: "ollama" | "local" | "rbac" | string;
  modelo?: string | null;
  mensaje?: unknown;
}

export interface ChatEstado {
  motor_configurado: "ollama" | "local" | string;
  ollama_disponible: boolean;
  ollama_version: string | null;
  ollama_url: string | null;
  modelo: string | null;
  modelo_instalado: boolean;
  modelos_disponibles: string[];
  detalle: string;
}

export interface ChatMensaje {
  id: number;
  sesion_id: number;
  rol: string;
  contenido: string;
  fecha_creacion: string;
}

// ===========================================================================
// MÓDULOS DE LAS HISTORIAS DE USUARIO UH-09 a UH-32
// ===========================================================================

/** PQRS (UH-09 · UH-16 · UH-32). */
export interface Pqrs {
  id: number;
  radicado: string;
  usuario_id?: number | null;
  tipo: string;
  categoria: string;
  asunto: string;
  descripcion: string;
  adjunto?: string | null;
  estado: "pendiente" | "en_proceso" | "cerrada" | string;
  respuesta?: string | null;
  respondido_por?: number | null;
  respondido_por_nombre?: string | null;
  fecha_respuesta?: string | null;
  fecha_creacion: string;
  solicitante?: string | null;
  apartamento?: string | null;
}

/** Zona común reservable (UH-10 · UH-14). */
export interface ZonaComun {
  id: number;
  nombre: string;
  descripcion?: string | null;
  capacidad: number;
  hora_apertura?: string | null;
  hora_cierre?: string | null;
  requiere_aprobacion: boolean;
  activo: boolean;
}

export interface ReservaZona {
  id: number;
  zona_id: number;
  zona_nombre?: string | null;
  usuario_id?: number | null;
  solicitante?: string | null;
  fecha: string;
  hora_inicio: string;
  hora_fin: string;
  motivo?: string | null;
  asistentes?: number | null;
  estado: string;
  motivo_decision?: string | null;
  fecha_creacion: string;
}

/** Comunicado / circular (UH-11 · UH-18). */
export interface Comunicado {
  id: number;
  titulo: string;
  contenido: string;
  categoria: string;
  prioridad: string;
  fijado: boolean;
  enviado_por?: number | null;
  autor?: string | null;
  fecha_creacion: string;
}

/** Visitante registrado en portería (UH-12). */
export interface Visitante {
  id: number;
  nombre: string;
  documento: string;
  telefono?: string | null;
  apartamento: string;
  residente_id?: number | null;
  motivo?: string | null;
  observaciones?: string | null;
  hora_ingreso: string;
  hora_salida?: string | null;
  estado: string;
  registrado_por?: number | null;
  registrado_por_nombre?: string | null;
}

/** Comprobante de pago (UH-13). */
export interface ComprobantePago {
  id: number;
  usuario_id: number;
  solicitante?: string | null;
  movimiento_id?: number | null;
  periodo?: string | null;
  monto: number;
  ruta_archivo: string;
  nombre_archivo?: string | null;
  mime?: string | null;
  tamano?: number | null;
  estado: string;
  observacion?: string | null;
  revisado_por?: number | null;
  fecha_revision?: string | null;
  fecha_creacion: string;
}

/** Estado de cuenta del residente (UH-17). */
export interface EstadoCuenta {
  usuario: { id: number; nombre: string; correo: string };
  unidades: { id: number; apartamento: string; torre?: string; bloque?: string }[];
  sin_unidad: boolean;
  total_facturado: number;
  total_pagado: number;
  saldo: number;
  proximo_vencimiento?: string | null;
  movimientos: {
    id: number;
    concepto: string;
    tipo: string;
    monto: number;
    fecha_vencimiento: string;
    fecha_pago?: string | null;
    estado: string;
    numero_recibo?: string | null;
    propiedad?: string | null;
  }[];
  comprobantes: ComprobantePago[];
  generado: string;
}

/** Votación del consejo (UH-25). */
export interface Votacion {
  id: number;
  titulo: string;
  descripcion?: string | null;
  fecha_cierre: string;
  estado: string;
  creado_por?: number | null;
  fecha_creacion: string;
  opciones: { id: number; texto: string; votos: number; porcentaje: number }[];
  total_votos: number;
  mi_voto?: number | null;
  puede_votar: boolean;
}

/** Solicitud que decide el consejo (UH-24). */
export interface Aprobacion {
  id: number;
  titulo: string;
  descripcion: string;
  monto: number;
  categoria: string;
  estado: string;
  creado_por?: number | null;
  creado_por_nombre?: string | null;
  decidido_por?: number | null;
  decidido_por_nombre?: string | null;
  fecha_decision?: string | null;
  motivo_decision?: string | null;
  fecha_creacion: string;
}

/** Registro del historial de auditoría (UH-29). */
export interface RegistroAuditoria {
  id: number;
  usuario_id?: number | null;
  usuario_nombre?: string | null;
  usuario_rol?: string | null;
  accion: string;
  modulo: string;
  metodo?: string | null;
  ruta?: string | null;
  entidad?: string | null;
  entidad_id?: number | null;
  detalle?: string | null;
  ip?: string | null;
  estado_http?: number | null;
  fecha_creacion: string;
}

/** Perfil propio del usuario (UH-20). */
export interface Perfil {
  id: number;
  nombre: string;
  telefono?: string | null;
  correo: string;
  rol_id: number;
  nombre_rol?: string;
  foto?: string | null;
  ultimo_acceso?: string | null;
  fecha_creacion?: string | null;
  preferencias?: { correo: boolean; push: boolean };
}

// ===========================================================================
// MENSAJERÍA DIRECTA: CHAT RESIDENTE <-> ADMINISTRACIÓN
// ===========================================================================

export interface ConversacionDirecta {
  id: number;
  residente_usuario_id: number;
  residente_nombre: string;
  residente_correo?: string | null;
  residente_telefono?: string | null;
  residente_foto?: string | null;
  apartamento?: string | null;
  id_conjunto?: number | null;
  nombre_conjunto?: string | null;
  asunto: string;
  estado: "abierta" | "resuelta" | string;
  ultimo_mensaje?: string | null;
  ultimo_mensaje_en?: string | null;
  ultimo_remitente_rol?: "residente" | "admin" | string | null;
  no_leidos: number;
  total_mensajes: number;
  fecha_creacion: string;
}

export interface MensajeDirecto {
  id: number;
  conversacion_id: number;
  remitente_id?: number | null;
  remitente_nombre?: string | null;
  remitente_foto?: string | null;
  rol_remitente: "residente" | "admin" | string;
  contenido: string;
  adjunto?: string | null;
  adjunto_nombre?: string | null;
  adjunto_mime?: string | null;
  leido: boolean;
  fecha_lectura?: string | null;
  fecha_creacion: string;
}

export interface ContactoChat {
  usuario_id: number;
  nombre: string;
  correo: string;
  telefono?: string | null;
  foto?: string | null;
  apartamento?: string | null;
  conversacion_id?: number | null;
}

export interface ResumenNoLeidos {
  no_leidos: number;
  conversaciones_sin_leer: number;
}

