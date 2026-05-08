import CardAction from "./CardAction";

interface ReporteItem {
  titulo: string;
  contenido: string[];
  textoBoton: string;
  alerta: string;
}

const Reportes = () => {
  const manejarAccion = (alerta: string) => {
    alert(alerta);
  };

  const reportes: ReporteItem[] = [
    {
      titulo: "- Horarios -",
      contenido: ["Lunes 1:00pm - 6:00pm", "Conjunto La Esperanza"],
      textoBoton: "Ver Horarios",
      alerta: "Horarios:\n- Lunes 1:00pm - 6:00pm | La Esperanza\n- Viernes 8:00am - 12:00pm | Asamblea",
    },
    {
      titulo: "- Mantenimientos -",
      contenido: ["Ninguno programado"],
      textoBoton: "Ver Mantenimientos",
      alerta: "Mantenimientos:\n- Ninguno programado actualmente",
    },
    {
      titulo: "- Deudas -",
      contenido: ["Mario Castañeda - Apto 101", "Administración"],
      textoBoton: "Ver Deudas",
      alerta: "Deudas pendientes:\n- Mario Castañeda - Apto 101\n- Carlos Ruiz - Apto 203",
    },
    {
      titulo: "- Reuniones -",
      contenido: ["Viernes 8:00am - 12:00pm", "Asamblea Extraordinaria"],
      textoBoton: "Ver Reuniones",
      alerta: "Reuniones:\n- Viernes 8:00am | Asamblea Extraordinaria",
    },
  ];

  return (
    <main style={{ flex: 1, padding: "2rem", backgroundColor: "#77836e" }}>
      <h2>Reportes</h2>
      <p style={{ fontSize: "1rem", color: "#0b0c0b" }}>
        Seleccione un reporte para consultar
      </p>

      <div style={{ display: "flex", flexDirection: "row", flexWrap: "nowrap", gap: "1rem", marginTop: "1rem", }}>
        {reportes.map((reporte) => (
          <div
            key={reporte.titulo}
            style={{
              border: "2px solid #77836e",
              padding: "1rem",
              borderRadius: "4px",
              width: "200px",
              minHeight: "150px",
              backgroundColor: "#759957",
            }}>

            <h3 style={{ marginBottom: "0.5rem", fontSize: "1rem", color: "#0b0c0b" }}>
              {reporte.titulo}
            </h3>
            {reporte.contenido.map((linea) => (
              <p key={linea} style={{ fontSize: "0.85rem", color: "#0b0c0b" }}>
                {linea}
              </p>
            ))}
            <CardAction
              titulo={reporte.titulo}
              descripcion=""
              textoBoton={reporte.textoBoton}
              onAccion={() => manejarAccion(reporte.alerta)}
            />
          </div>
        ))}
      </div>
    </main>
  );
};

export default Reportes;