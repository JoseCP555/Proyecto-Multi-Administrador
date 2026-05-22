import { useState } from "react";
import { useNavigate } from "react-router-dom";
import CardAction from "./CardAction";

const Registro = () => {
  const navigate = useNavigate();
  const [nombre, setNombre] = useState<string>("");
  const [correo, setCorreo] = useState<string>("");
  const [contraseña, setContraseña] = useState<string>("");
  const [verResultado, setVerResultado] = useState<boolean>(false);

  const manejarAccion = () => {

    alert(`Cuenta registrada para ${nombre}`);

    navigate("/");
  };

  return (
    <main style={{
      minHeight: "100vh",
      display: "flex",
      justifyContent: "center",
      alignItems: "center"
    }}>
      <div style={{
        border: "2px solid #afeba4",
        borderRadius: "4px",
        backgroundColor: "#77836e",
        padding: "2rem",
        width: "350px",
        textAlign: "center"
      }}>
        <h2>Registro de Usuarios</h2>
        <p style={{ color: "#e8f5e1" }}>Crear nueva cuenta</p>

        <input
          type="text"
          placeholder="Nombre"
          value={nombre}
          onChange={(e) => setNombre(e.target.value)}
          style={{ width: "250px", padding: "0.5rem", display: "block", margin: "0 auto 1rem auto" }}
        />

        <input
          type="text"
          placeholder="Correo"
          value={correo}
          onChange={(e) => setCorreo(e.target.value)}
          style={{ width: "250px", padding: "0.5rem", display: "block", margin: "0 auto 1rem auto" }}
        />

        <input
          type="password"
          placeholder="Contraseña"
          value={contraseña}
          onChange={(e) => setContraseña(e.target.value)}
          style={{ width: "250px", padding: "0.5rem", display: "block", margin: "0 auto 1rem auto" }}
        />

        <CardAction
          titulo="Registrarse"
          descripcion=""
          textoBoton="Registrarse"
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
            <p style={{ margin: "0.3rem 0" }}>Correo: <strong>{correo}</strong></p>
            <p style={{ margin: "0.3rem 0" }}>Contraseña: <strong>{contraseña}</strong></p>
          </div>
        )}
      </div>
    </main>
  );
};

export default Registro;