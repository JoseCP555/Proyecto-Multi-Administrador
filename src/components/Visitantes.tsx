import { useState } from "react";
import CardAccion from "./CardAction";

const Visitantes = () => {
  const [nombre, setNombre] = useState<string>("");
  const [documento, setDocumento] = useState<string>("");
  const [apartamento, setApartamento] = useState<string>("");
  const [motivo, setMotivo] = useState<string>("");
  const [verResultado, setVerResultado] = useState<boolean>(false);

  const manejarAccion = () => {
    alert(`[Módulo: Visitantes]\nNombre: ${nombre}\nDocumento: ${documento}\nApartamento: ${apartamento}\nMotivo: ${motivo}`);
  };

  return (
    <main style={{
      flex: 1,
      padding: "1rem",
      display: "flex",
      justifyContent: "center",
    }}>
      <div style={{
        border: "2px solid #afeba4",
        borderRadius: "4px",
        backgroundColor: "#77836e",
        padding: "2rem",
        width: "350px",
        textAlign: "center",
        alignSelf: "flex-start"
      }}>
        <h2>Registro de Visitantes</h2>
        <p style={{ color: "#e8f5e1" }}>Ingrese los datos del visitante</p>

        <input
          type="text"
          placeholder="Nombre completo"
          value={nombre}
          onChange={(e) => setNombre(e.target.value)}
          style={{ width: "270px", padding: "0.5rem", display: "block", margin: "0 auto 1rem auto" }}
        />

        <input
          type="text"
          placeholder="Número de documento"
          value={documento}
          onChange={(e) => setDocumento(e.target.value)}
          style={{ width: "270px", padding: "0.5rem", display: "block", margin: "0 auto 1rem auto" }}
        />

        <input
          type="text"
          placeholder="Apartamento a visitar"
          value={apartamento}
          onChange={(e) => setApartamento(e.target.value)}
          style={{ width: "270px", padding: "0.5rem", display: "block", margin: "0 auto 1rem auto" }}
        />

        <select
          value={motivo}
          onChange={(e) => setMotivo(e.target.value)}
          style={{ width: "285px", padding: "0.5rem", display: "block", margin: "0 auto 1rem auto" }}
        >
          <option value="">Seleccione el motivo</option>
          <option value="Visita familiar">Visita familiar</option>
          <option value="Domicilio">Domicilio</option>
          <option value="Mantenimiento">Mantenimiento</option>
          <option value="Otro">Otro</option>
        </select>

        <CardAccion
          titulo="Registrar"
          descripcion=""
          textoBoton="Registrar Visitante"
          onAccion={manejarAccion}
        />

        <button
          onClick={() => setVerResultado(!verResultado)}
          style={{
            marginTop: "0.8rem",
            padding: "0.5rem 1rem",
            backgroundColor: "#4e7750",
            color: "white",
            border: "none",
            borderRadius: "4px",
            cursor: "pointer",
            fontWeight: "bold"
          }}
        >
          {verResultado ? "Ocultar datos" : "Mostrar datos"}
        </button>

        {verResultado && (
          <div style={{
            marginTop: "1rem",
            backgroundColor: "#5a6e52",
            border: "1px solid #afeba4",
            borderRadius: "4px",
            padding: "0.8rem",
            color: "#e8f5e1",
            textAlign: "left"
          }}>
            <p style={{ margin: "0.3rem 0" }}>Nombre: <strong>{nombre}</strong></p>
            <p style={{ margin: "0.3rem 0" }}>Documento: <strong>{documento}</strong></p>
            <p style={{ margin: "0.3rem 0" }}>Apartamento: <strong>{apartamento}</strong></p>
            <p style={{ margin: "0.3rem 0" }}>Motivo: <strong>{motivo}</strong></p>
          </div>
        )}
      </div>
    </main>
  );
};

export default Visitantes;