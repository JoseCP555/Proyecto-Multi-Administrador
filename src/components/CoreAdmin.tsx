import { useState } from "react";

interface Admin {
  nombre: string;
  rol: string;
  sucursal: string;
}

interface Actividad {
  id: number;
  admin: string;
  accion: string;
  hora: string;
  tipo: string;
}

interface Tema {
  bg: string;
  texto: string;
  sidebar: string;
  cardBg: string;
  borde: string;
  primario: string;
  exito: string;
  peligro: string;
}

interface CardAccionProps {
  titulo: string;
  descripcion: string;
  textoBoton?: string;
  onAccion: (info: string) => void;
}

function CardAccion({ titulo, textoBoton = "Ejecutar", onAccion }: CardAccionProps) {
  return (
    <button
      onClick={() => onAccion(titulo || textoBoton)}
      style={{
        display: "block",
        margin: "0 auto",
        width: "70%",
        padding: "1.2rem 1rem",
        backgroundColor: "#4e7750",
        color: "white",
        border: "none",
        borderRadius: "6px",
        cursor: "pointer",
        fontSize: "0.85rem",
        fontWeight: "bold",
        whiteSpace: "normal",
        textAlign: "center",
      }}
    >
      {textoBoton}
    </button>
  );
}

function Dashboard() {
  const [adminActual, setAdminActual] = useState<Admin>({
    nombre: "Carlos Mendoza",
    rol: "SuperAdmin",
    sucursal: "Central",
  });

  const [usuarios, setUsuarios] = useState(1240);
  const [productos, setProductos] = useState(382);
  const [ingresos, setIngresos] = useState(15420);

  const [actividades, setActividades] = useState<Actividad[]>([
    { id: 1, admin: "Carlos M.", accion: "Actualizó stock de iPhone 15", hora: "Hace 5 min", tipo: "update" },
    { id: 2, admin: "Laura R. (Ventas)", accion: "Aprobó reembolso #4821", hora: "Hace 20 min", tipo: "approve" },
    { id: 3, admin: "Carlos M.", accion: "Creó nuevo perfil de administrador (Soporte)", hora: "Hace 1 hora", tipo: "create" },
  ]);

  const tema: Tema = {
    bg: "#f8fafc",
    texto: "#0f172a",
    sidebar: "#1e293b",
    cardBg: "#ffffff",
    borde: "#e2e8f0",
    primario: "#3b82f6",
    exito: "#10b981",
    peligro: "#ef4444",
  };

  const registrarActividad = (accion: string) => {
    const nueva: Actividad = {
      id: Date.now(),
      admin: adminActual.nombre,
      accion,
      hora: "Ahora mismo",
      tipo: "approve",
    };
    setActividades((prev) => [nueva, ...prev]);
  };

  const simularVenta = () => {
    setIngresos((prev) => prev + 150);
    registrarActividad("Registró una venta manual (+ $150 USD)");
  };

  const crearUsuario = () => {
    setUsuarios((prev) => prev + 1);
    registrarActividad("Creó un nuevo usuario");
  };

  const recibirLote = () => {
    setProductos((prev) => prev + 5);
    registrarActividad("Recibió lote de inventario (+5)");
  };

  const cambiarRolSimulado = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const rolSeleccionado = e.target.value;
    setAdminActual({
      ...adminActual,
      rol: rolSeleccionado,
      nombre: rolSeleccionado === "SuperAdmin" ? "Carlos Mendoza" : "Laura Rodríguez",
    });
  };

  return (
    <div style={{ display: "flex", minHeight: "100vh", backgroundColor: tema.bg, fontFamily: "system-ui, sans-serif" }}>

      {/* SIDEBAR */}
      <div style={{ width: "260px", backgroundColor: tema.sidebar, color: "white", padding: "24px", display: "flex", flexDirection: "column", justifyContent: "space-between" }}>
        <div>
          <h2 style={{ fontSize: "1.3rem", fontWeight: "bold", marginBottom: "30px", borderBottom: "1px solid #334155", paddingBottom: "10px" }}>
            Multi-Admin
          </h2>
          <nav style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
            <div style={{ padding: "10px", backgroundColor: "#334155", borderRadius: "6px", cursor: "pointer" }}>Panel General</div>
            <div style={{ padding: "10px", borderRadius: "6px", cursor: "pointer", opacity: 0.7 }}>Gestión de Admins</div>
            <div style={{ padding: "10px", borderRadius: "6px", cursor: "pointer", opacity: 0.7 }}>Inventario Global</div>
            <div style={{ padding: "10px", borderRadius: "6px", cursor: "pointer", opacity: 0.7 }}>Configuraciones</div>
          </nav>
        </div>

        <div style={{ marginTop: "auto", padding: "15px", backgroundColor: "#334155", borderRadius: "8px" }}>
          <p style={{ margin: 0, fontSize: "0.85rem", opacity: 0.7 }}>Sesión activa:</p>
          <strong style={{ display: "block", fontSize: "1rem" }}>{adminActual.nombre}</strong>
          <span style={{ fontSize: "0.8rem", backgroundColor: tema.primario, padding: "2px 6px", borderRadius: "4px", display: "inline-block", marginTop: "5px" }}>
            {adminActual.rol}
          </span>
        </div>
      </div>

      {/* CONTENIDO PRINCIPAL */}
      <div style={{ flex: 1, padding: "30px", overflowY: "auto" }}>

        {/* HEADER */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "30px", borderBottom: `1px solid ${tema.borde}`, paddingBottom: "20px" }}>
          <div>
            <h1 style={{ margin: 0, color: tema.texto, fontSize: "1.8rem" }}>Dashboard Corporativo</h1>
            <p style={{ color: "#64748b", margin: "5px 0 0 0" }}>
              Sucursal: <strong>{adminActual.sucursal}</strong>
            </p>
          </div>

          <div style={{ backgroundColor: "#e2e8f0", padding: "10px", borderRadius: "8px" }}>
            <label style={{ fontSize: "0.85rem", marginRight: "10px", fontWeight: "bold" }}>Simular Rol:</label>
            <select
              onChange={cambiarRolSimulado}
              value={adminActual.rol}
              style={{ padding: "5px", borderRadius: "4px", border: "1px solid #cbd5e1" }}
            >
              <option value="SuperAdmin">SuperAdmin (Carlos)</option>
              <option value="AdminVentas">Admin de Ventas (Laura)</option>
            </select>
          </div>
        </div>

        {/* TARJETAS CON CardAccion */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: "20px", marginBottom: "30px" }}>

          <div style={cardStyle(tema)}>
            <h3 style={cardTitleStyle}>Ingresos Totales</h3>
            <p style={cardValueStyle(tema)}>${ingresos.toLocaleString()} USD</p>
            {(adminActual.rol === "SuperAdmin" || adminActual.rol === "AdminVentas") ? (
              <CardAccion
                titulo="Ingresos Totales"
                descripcion="Registra una venta manual"
                textoBoton="+ Registrar Venta"
                onAccion={simularVenta}
              />
            ) : (
              <p style={{ fontSize: "0.8rem", color: tema.peligro, margin: 0 }}>Sin permisos de edición</p>
            )}
          </div>

          <div style={cardStyle(tema)}>
            <h3 style={cardTitleStyle}>Usuarios Registrados</h3>
            <p style={cardValueStyle(tema)}>{usuarios}</p>
            {adminActual.rol === "SuperAdmin" && (
              <CardAccion
                titulo="Usuarios Registrados"
                descripcion="Crea un nuevo usuario"
                textoBoton="+ Crear Usuario"
                onAccion={crearUsuario}
              />
            )}
          </div>

          <div style={cardStyle(tema)}>
            <h3 style={cardTitleStyle}>Productos en Stock</h3>
            <p style={cardValueStyle(tema)}>{productos} ítems</p>
            <CardAccion
              titulo="Productos en Stock"
              descripcion="Recibe un lote de inventario"
              textoBoton="Recibir Lote (+5)"
              onAccion={recibirLote}
            />
          </div>

        </div>

        {/* LOG DE AUDITORÍA */}
        <div style={{ backgroundColor: tema.cardBg, padding: "24px", borderRadius: "12px", boxShadow: "0 1px 3px rgba(0,0,0,0.05)", border: `1px solid ${tema.borde}` }}>
          <h2 style={{ fontSize: "1.2rem", color: tema.texto, marginBottom: "15px" }}>
            Historial de Auditoría Global
          </h2>
          <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
            {actividades.map((act) => (
              <div
                key={act.id}
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  padding: "12px",
                  backgroundColor: "#f8fafc",
                  borderRadius: "8px",
                  borderLeft: `4px solid ${act.tipo === "approve" ? tema.exito : tema.primario}`,
                }}
              >
                <div>
                  <span style={{ fontWeight: "bold", color: tema.texto }}>{act.admin}</span>
                  <span style={{ marginLeft: "8px", color: "#334155" }}>{act.accion}</span>
                </div>
                <span style={{ fontSize: "0.85rem", color: "#94a3b8" }}>{act.hora}</span>
              </div>
            ))}
          </div>
        </div>

      </div>
    </div>
  );
}

// Estilos auxiliares
const cardStyle = (tema: Tema): React.CSSProperties => ({
  backgroundColor: tema.cardBg,
  padding: "24px",
  borderRadius: "12px",
  boxShadow: "0 1px 3px rgba(0,0,0,0.05)",
  border: `1px solid ${tema.borde}`,
  display: "flex",
  flexDirection: "column",
  gap: "8px",
});

const cardTitleStyle: React.CSSProperties = {
  margin: 0,
  fontSize: "0.95rem",
  color: "#64748b",
  fontWeight: 500,
};

const cardValueStyle = (tema: Tema): React.CSSProperties => ({
  margin: 0,
  fontSize: "1.8rem",
  fontWeight: "bold",
  color: tema.texto,
});

export default Dashboard;
