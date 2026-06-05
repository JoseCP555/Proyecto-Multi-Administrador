import { useState } from "react";
import CardAccion from "./CardAction";

const Usuarios = () => {
  const [mostrarInfo, setMostrarInfo] = useState<boolean>(false);

  const manejarAccion = (accion: string) => {
    alert(`[Módulo: Usuarios] Acción realizada: ${accion}`);
  };

  return (
    <main style={{ flex: 1, padding: "2rem", backgroundColor: "#b7b9b5" }}>
      <h2>Bienvenido Administrador</h2>
      <p style={{ fontSize: "1rem", color: "#0b0c0b" }}>
        ¿Qué hay para hacer hoy?
      </p>

      <button
        onClick={() => setMostrarInfo(!mostrarInfo)}
        style={{
          marginBottom: "1rem",
          padding: "0.5rem 1rem",
          backgroundColor: "#4e7750",
          color: "white",
          border: "none",
          borderRadius: "4px",
          cursor: "pointer",
          fontWeight: "bold"
        }}
      >
        {mostrarInfo ? "Ocultar información" : "Ver información del conjunto"}
      </button>

      {mostrarInfo && (
        <div style={{
          display: "flex",
          flexDirection: "row",
          flexWrap: "nowrap",
          gap: "1rem",
          marginTop: "1rem",
          overflowX: "auto"
        }}>
          <div style={{
            padding: "1rem",
            borderRadius: "4px",
            width: "200px",
            minHeight: "150px",
            backgroundColor: "#759957",
          }}>
            <h3 style={{ marginBottom: "0.5rem", fontSize: "1rem", color: "#0b0c0b" }}>
              ─ Horarios ─
            </h3>
            <p style={{ fontSize: "0.85rem", color: "#0b0c0b" }}>Lunes 1:00pm - 6:00pm</p>
            <p style={{ fontSize: "0.85rem", color: "#0b0c0b" }}>Conjunto La Esperanza</p>
            <CardAccion
              titulo="Horarios"
              descripcion=""
              textoBoton="Ver"
              onAccion={manejarAccion}
            />
          </div>

          <div style={{
            padding: "1rem",
            borderRadius: "4px",
            width: "200px",
            minHeight: "150px",
            backgroundColor: "#759957",
          }}>
            <h3 style={{ marginBottom: "0.5rem", fontSize: "1rem", color: "#0b0c0b" }}>
              ─ Mantenimientos ─
            </h3>
            <p style={{ fontSize: "0.85rem", color: "#0b0c0b" }}>Ninguno</p>
            <CardAccion
              titulo="Mantenimientos"
              descripcion=""
              textoBoton="Ver"
              onAccion={manejarAccion}
            />
          </div>

          <div style={{
            padding: "1rem",
            borderRadius: "4px",
            width: "200px",
            minHeight: "150px",
            backgroundColor: "#759957",
          }}>
            <h3 style={{ marginBottom: "0.5rem", fontSize: "1rem", color: "#0b0c0b" }}>
              ─ Deudas ─
            </h3>
            <p style={{ fontSize: "0.85rem", color: "#0b0c0b" }}>Mario Castañeda - Apto 101</p>
            <p style={{ fontSize: "0.85rem", color: "#0b0c0b" }}>Administración</p>
            <CardAccion
              titulo="Deudas"
              descripcion=""
              textoBoton="Ver"
              onAccion={manejarAccion}
            />
          </div>

          <div style={{
            padding: "1rem",
            borderRadius: "4px",
            width: "200px",
            minHeight: "150px",
            backgroundColor: "#759957",
          }}>
            <h3 style={{ marginBottom: "0.5rem", fontSize: "1rem", color: "#0b0c0b" }}>
              ─ Reuniones ─
            </h3>
            <p style={{ fontSize: "0.85rem", color: "#0b0c0b" }}>Viernes 8:00am - 12:00pm</p>
            <p style={{ fontSize: "0.85rem", color: "#0b0c0b" }}>Asamblea Extraordinaria</p>
            <CardAccion
              titulo="Reuniones"
              descripcion=""
              textoBoton="Ver"
              onAccion={manejarAccion}
            />
          </div>
        </div>
      )}
    </main>
  );
};

export default Usuarios;