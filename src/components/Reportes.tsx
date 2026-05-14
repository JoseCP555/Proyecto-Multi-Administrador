import { useState } from "react";
import CardAction from "./CardAction";

interface ReporteItem {
  titulo: string;
  textoBoton: string;
  alerta: string;
}

const Reportes = () => {
  const [mostrarReportes, setMostrarReportes] = useState<boolean>(false);

  const manejarAccion = (alerta: string) => {
    alert(alerta);
  };

  const reportes: ReporteItem[] = [
    {
      titulo: "Horarios",
      textoBoton: "Ver Horarios",
      alerta: "Horarios:\n- Lunes 1:00pm - 6:00pm | La Esperanza\n- Viernes 8:00am - 12:00pm | Asamblea",
    },
    {
      titulo: "Mantenimientos",
      textoBoton: "Ver Mantenimientos",
      alerta: "Mantenimientos:\n- Ninguno programado actualmente",
    },
    {
      titulo: "Deudas",
      textoBoton: "Ver Deudas",
      alerta: "Deudas pendientes:\n- Mario Castañeda - Apto 101\n- Carlos Ruiz - Apto 203",
    },
    {
      titulo: "Reuniones",
      textoBoton: "Ver Reuniones",
      alerta: "Reuniones:\n- Viernes 8:00am | Asamblea Extraordinaria",
    },
  ];

  return (
    <main style={{ flex: 1, padding: "2rem", backgroundColor: "#b7b9b5", minHeight: "100vh" }}>
      <h2 style={{ color: "#0b0c0b" }}>Reportes</h2>
      <p style={{ color: "#0b0c0b" }}>Consulte la información del conjunto</p>

      <button
        onClick={() => setMostrarReportes(!mostrarReportes)}
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
        {mostrarReportes ? "Ocultar reportes" : "Ver reportes disponibles"}
      </button>

      {mostrarReportes && (
        <div style={{
          display: "flex",
          flexDirection: "row",
          flexWrap: "nowrap",
          gap: "1rem",
          overflowX: "auto"
        }}>
          {reportes.map((reporte) => (
          <div
            key={reporte.titulo}
            style={{
              padding: "1rem",
              borderRadius: "4px",
              width: "200px",
              minHeight: "150px",
              backgroundColor: "#759957",
            }}
          >
            <h3 style={{ fontSize: "1rem", color: "#0b0c0b", marginBottom: "0.5rem" }}>
              ─ {reporte.titulo} ─
            </h3>
            <CardAction
              titulo={reporte.titulo}
              descripcion=""
              textoBoton={reporte.textoBoton}
              onAccion={() => manejarAccion(reporte.alerta)}
            />
          </div>
        ))}
        </div>
      )}
    </main>
  );
};

export default Reportes;