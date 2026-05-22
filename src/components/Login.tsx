import { useState } from "react";
import CardAction from "./CardAction";

const Login = () => {
  const [usuario, setUsuario] = useState<string>("");
  const [contraseña, setContraseña] = useState<string>("");
  const [verResultado, setVerResultado] = useState<boolean>(false);

  const manejarAccion = () => {
    alert(`[Módulo: Login]\nUsuario: ${usuario}\nContraseña: ${contraseña}`);
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
        padding: "1rem",
        width: "300px",
        textAlign: "center",
        alignSelf: "flex-start"
      }}>
        <h2>Login de Usuario</h2>
        <p style={{ color: "#e8f5e1" }}>Ingrese sus datos</p>

        <input
          type="text"
          placeholder="Usuario"
          value={usuario}
          onChange={(e) => setUsuario(e.target.value)}
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
          titulo="Ingresar"
          descripcion=""
          textoBoton="Ingresar"
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
            <p style={{ margin: "0.3rem 0" }}>Usuario: <strong>{usuario}</strong></p>
            <p style={{ margin: "0.3rem 0" }}>Contraseña: <strong>{contraseña}</strong></p>
          </div>
        )}
      </div>
    </main>
  );
};

export default Login;