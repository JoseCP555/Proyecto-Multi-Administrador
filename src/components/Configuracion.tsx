import { useState, type ChangeEvent } from "react";
import CardAction from "./CardAction";

const Configuracion = () => {
  const [nombreAdmin, setNombreAdmin] = useState<string>("Carlos Mendoza");
  const [correoAdmin, setCorreoAdmin] = useState<string>("carlos@empresa.com");
  const [tema, setTema] = useState<string>("Oscuro");
  const [idioma, setIdioma] = useState<string>("Español");
  const [notificaciones, setNotificaciones] = useState<boolean>(true);
  const [modoPrivado, setModoPrivado] = useState<boolean>(false);
  const [mostrarResumen, setMostrarResumen] = useState<boolean>(true);

  const guardarCambios = () => {
    alert(
      `Configuración guardada\n\n` +
      `Administrador: ${nombreAdmin}\n` +
      `Correo: ${correoAdmin}\n` +
      `Tema: ${tema}\n` +
      `Idioma: ${idioma}\n` +
      `Notificaciones: ${notificaciones ? "Activas" : "Desactivadas"}\n` +
      `Modo privado: ${modoPrivado ? "Activo" : "Inactivo"}`
    );
  };

  const limpiarDatos = () => {
    setNombreAdmin("Carlos Mendoza");
    setCorreoAdmin("carlos@empresa.com");
    setTema("Oscuro");
    setIdioma("Español");
    setNotificaciones(true);
    setModoPrivado(false);
    setMostrarResumen(true);
  };

  return (
    <main
      style={{
        minHeight: "100vh",
        padding: "2rem",
        background:
          "linear-gradient(180deg, #0f172a 0%, #111827 45%, #e5e7eb 100%)",
        color: "#e5e7eb",
      }}
    >
      <div
        style={{
          maxWidth: "1100px",
          margin: "0 auto",
        }}
      >
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "flex-start",
            gap: "1rem",
            flexWrap: "wrap",
            marginBottom: "1.5rem",
          }}
        >
          <div>
            <h1 style={{ margin: 0, fontSize: "2rem", color: "#f8fafc" }}>
              Configuración
            </h1>
            <p style={{ marginTop: "0.35rem", color: "#cbd5e1" }}>
              Ajustes generales del administrador y preferencias del sistema
            </p>
          </div>

          <div
            style={{
              backgroundColor: "#1e293b",
              border: "1px solid #334155",
              borderRadius: "14px",
              padding: "1rem 1.25rem",
              minWidth: "260px",
              boxShadow: "0 10px 30px rgba(0,0,0,0.18)",
            }}
          >
            <p style={{ margin: 0, color: "#94a3b8", fontSize: "0.9rem" }}>
              Sesión activa
            </p>
            <h3 style={{ margin: "0.25rem 0 0", color: "#f8fafc" }}>
              {nombreAdmin}
            </h3>
            <p style={{ margin: "0.2rem 0 0", color: "#86efac" }}>
              Administrador principal
            </p>
          </div>
        </div>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(360px, 1fr))",
            gap: "1.25rem",
          }}
        >
          <section
            style={{
              backgroundColor: "#ffffff",
              color: "#0f172a",
              borderRadius: "16px",
              padding: "1.5rem",
              boxShadow: "0 12px 28px rgba(15,23,42,0.14)",
              border: "1px solid #dbe4f0",
            }}
          >
            <h2 style={{ marginTop: 0, marginBottom: "1rem" }}>
              Datos principales
            </h2>

            <label style={{ display: "block", marginBottom: "0.9rem" }}>
              <span
                style={{
                  display: "block",
                  marginBottom: "0.4rem",
                  fontWeight: 600,
                }}
              >
                Nombre del administrador
              </span>
              <input
                type="text"
                value={nombreAdmin}
                onChange={(e: ChangeEvent<HTMLInputElement>) =>
                  setNombreAdmin(e.target.value)
                }
                placeholder="Nombre del administrador"
                style={{
                  width: "100%",
                  padding: "0.70rem 0.85rem",
                  borderRadius: "10px",
                  border: "1px solid #cbd5e1",
                  outline: "none",
                  fontSize: "0.92rem",
                  boxSizing: "border-box",
                }}
              />
            </label>

            <label style={{ display: "block", marginBottom: "0.9rem" }}>
              <span
                style={{
                  display: "block",
                  marginBottom: "0.4rem",
                  fontWeight: 600,
                }}
              >
                Correo electrónico
              </span>
              <input
                type="email"
                value={correoAdmin}
                onChange={(e: ChangeEvent<HTMLInputElement>) =>
                  setCorreoAdmin(e.target.value)
                }
                placeholder="correo@empresa.com"
                style={{
                  width: "100%",
                  padding: "0.70rem 0.85rem",
                  borderRadius: "10px",
                  border: "1px solid #cbd5e1",
                  outline: "none",
                  fontSize: "0.92rem",
                  boxSizing: "border-box",
                }}
              />
            </label>

            <label style={{ display: "block", marginBottom: "0.9rem" }}>
              <span
                style={{
                  display: "block",
                  marginBottom: "0.4rem",
                  fontWeight: 600,
                }}
              >
                Tema visual
              </span>
              <select
                value={tema}
                onChange={(e: ChangeEvent<HTMLSelectElement>) =>
                  setTema(e.target.value)
                }
                style={{
                  width: "100%",
                  padding: "0.70rem 0.85rem",
                  borderRadius: "10px",
                  border: "1px solid #cbd5e1",
                  outline: "none",
                  fontSize: "0.92rem",
                  backgroundColor: "#fff",
                  boxSizing: "border-box",
                }}
              >
                <option value="Oscuro">Oscuro</option>
                <option value="Claro">Claro</option>
                <option value="Verde corporativo">Verde corporativo</option>
              </select>
            </label>

            <label style={{ display: "block" }}>
              <span
                style={{
                  display: "block",
                  marginBottom: "0.4rem",
                  fontWeight: 600,
                }}
              >
                Idioma
              </span>
              <select
                value={idioma}
                onChange={(e: ChangeEvent<HTMLSelectElement>) =>
                  setIdioma(e.target.value)
                }
                style={{
                  width: "100%",
                  padding: "0.70rem 0.85rem",
                  borderRadius: "10px",
                  border: "1px solid #cbd5e1",
                  outline: "none",
                  fontSize: "0.92rem",
                  backgroundColor: "#fff",
                  boxSizing: "border-box",
                }}
              >
                <option value="Español">Español</option>
                <option value="Inglés">Inglés</option>
              </select>
            </label>
          </section>

          <section
            style={{
              backgroundColor: "#ffffff",
              color: "#0f172a",
              borderRadius: "16px",
              padding: "1.5rem",
              boxShadow: "0 12px 28px rgba(15,23,42,0.14)",
              border: "1px solid #dbe4f0",
            }}
          >
            <h2 style={{ marginTop: 0, marginBottom: "1rem" }}>
              Preferencias del sistema
            </h2>

            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                padding: "0.95rem 1rem",
                borderRadius: "12px",
                backgroundColor: "#f8fafc",
                border: "1px solid #e2e8f0",
                marginBottom: "0.9rem",
              }}
            >
              <div>
                <strong>Notificaciones</strong>
                <p style={{ margin: "0.25rem 0 0", color: "#64748b" }}>
                  Recibir alertas y avisos del sistema
                </p>
              </div>

              <button
                onClick={() => setNotificaciones(!notificaciones)}
                style={{
                  padding: "0.6rem 1rem",
                  borderRadius: "999px",
                  border: "none",
                  cursor: "pointer",
                  fontWeight: 700,
                  backgroundColor: notificaciones ? "#166534" : "#475569",
                  color: "white",
                }}
              >
                {notificaciones ? "Activas" : "Desactivadas"}
              </button>
            </div>

            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                padding: "0.95rem 1rem",
                borderRadius: "12px",
                backgroundColor: "#f8fafc",
                border: "1px solid #e2e8f0",
                marginBottom: "1rem",
              }}
            >
              <div>
                <strong>Modo privado</strong>
                <p style={{ margin: "0.25rem 0 0", color: "#64748b" }}>
                  Ocultar información sensible en pantalla
                </p>
              </div>

              <button
                onClick={() => setModoPrivado(!modoPrivado)}
                style={{
                  padding: "0.6rem 1rem",
                  borderRadius: "999px",
                  border: "none",
                  cursor: "pointer",
                  fontWeight: 700,
                  backgroundColor: modoPrivado ? "#334155" : "#4e7750",
                  color: "white",
                }}
              >
                {modoPrivado ? "Activo" : "Inactivo"}
              </button>
            </div>

            <div style={{ display: "flex", gap: "0.75rem", flexWrap: "wrap" }}>
              <CardAction
                titulo="Guardar configuración"
                descripcion=""
                textoBoton="Guardar cambios"
                onAccion={guardarCambios}
              />

              <button
                onClick={limpiarDatos}
                style={{
                  padding: "0.85rem 1.1rem",
                  borderRadius: "10px",
                  border: "1px solid #cbd5e1",
                  backgroundColor: "#e2e8f0",
                  color: "#0f172a",
                  cursor: "pointer",
                  fontWeight: 700,
                }}
              >
                Restaurar
              </button>

              <button
                onClick={() => setMostrarResumen(!mostrarResumen)}
                style={{
                  padding: "0.85rem 1.1rem",
                  borderRadius: "10px",
                  border: "none",
                  backgroundColor: "#1d4ed8",
                  color: "white",
                  cursor: "pointer",
                  fontWeight: 700,
                }}
              >
                {mostrarResumen ? "Ocultar resumen" : "Mostrar resumen"}
              </button>
            </div>
          </section>
        </div>

        {mostrarResumen && (
          <section
            style={{
              marginTop: "1.25rem",
              backgroundColor: "#0f172a",
              color: "#e2e8f0",
              borderRadius: "16px",
              padding: "1.5rem",
              border: "1px solid #334155",
              boxShadow: "0 12px 28px rgba(15,23,42,0.2)",
            }}
          >
            <h2 style={{ marginTop: 0, color: "#f8fafc" }}>Resumen actual</h2>

            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
                gap: "0.9rem",
              }}
            >
              <div
                style={{
                  backgroundColor: "#111827",
                  border: "1px solid #334155",
                  borderRadius: "12px",
                  padding: "1rem",
                }}
              >
                <p style={{ margin: 0, color: "#94a3b8" }}>Administrador</p>
                <strong style={{ fontSize: "1.05rem" }}>{nombreAdmin}</strong>
              </div>

              <div
                style={{
                  backgroundColor: "#111827",
                  border: "1px solid #334155",
                  borderRadius: "12px",
                  padding: "1rem",
                }}
              >
                <p style={{ margin: 0, color: "#94a3b8" }}>Correo</p>
                <strong style={{ fontSize: "1.05rem" }}>{correoAdmin}</strong>
              </div>

              <div
                style={{
                  backgroundColor: "#111827",
                  border: "1px solid #334155",
                  borderRadius: "12px",
                  padding: "1rem",
                }}
              >
                <p style={{ margin: 0, color: "#94a3b8" }}>Tema</p>
                <strong style={{ fontSize: "1.05rem" }}>{tema}</strong>
              </div>

              <div
                style={{
                  backgroundColor: "#111827",
                  border: "1px solid #334155",
                  borderRadius: "12px",
                  padding: "1rem",
                }}
              >
                <p style={{ margin: 0, color: "#94a3b8" }}>Idioma</p>
                <strong style={{ fontSize: "1.05rem" }}>{idioma}</strong>
              </div>
            </div>
          </section>
        )}
      </div>
    </main>
  );
};

export default Configuracion;