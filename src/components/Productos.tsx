import { useState } from "react";
import CardAccion from "./CardAction";

const Productos = () => {
  const [mostrarMenu, setMostrarMenu] = useState<boolean>(false);

  const mostrarAccion = (accion: string) => {
    alert(`[Módulo: Productos] Se seleccionó: ${accion}`);
  };

  return (
    <aside style={{
      width: "280px",
      minHeight: "100vh",
      padding: "1rem",
      backgroundColor: "#77836e",
      display: "flex",
      flexDirection: "column",
      gap: "1rem"
    }}>
      <h2 style={{ color: "white", textAlign: "center" }}>
        Funciones Administrador
      </h2>

      <button
        onClick={() => setMostrarMenu(!mostrarMenu)}
        style={{
          padding: "0.6rem 1rem",
          backgroundColor: "#4e7750",
          color: "white",
          border: "none",
          borderRadius: "4px",
          cursor: "pointer",
          fontWeight: "bold"
        }}
      >
        {mostrarMenu ? "Ocultar funciones" : "Ver funciones"}
      </button>

      {mostrarMenu && (
        <>
          <CardAccion
            titulo="Conjuntos"
            descripcion=""
            textoBoton="Conjuntos"
            onAccion={mostrarAccion}
          />
          <CardAccion
            titulo="Horarios"
            descripcion=""
            textoBoton="Horarios"
            onAccion={mostrarAccion}
          />
          <CardAccion
            titulo="Finanzas"
            descripcion=""
            textoBoton="Finanzas"
            onAccion={mostrarAccion}
          />
          <CardAccion
            titulo="Proveedores"
            descripcion=""
            textoBoton="Proveedores"
            onAccion={mostrarAccion}
          />
          <CardAccion
            titulo="Documentos"
            descripcion=""
            textoBoton="Documentos"
            onAccion={mostrarAccion}
          />
          <CardAccion
            titulo="Mantenimientos"
            descripcion=""
            textoBoton="Mantenimientos"
            onAccion={mostrarAccion}
          />
          <CardAccion
            titulo="Configuración"
            descripcion=""
            textoBoton="Configuración"
            onAccion={mostrarAccion}
          />
        </>
      )}
    </aside>
  );
};

export default Productos;