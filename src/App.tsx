import { Routes, Route, Link } from "react-router-dom";

import Usuarios from "./components/Usuarios";
import Productos from "./components/Productos";
import Login from "./components/Login";
import Registro from "./components/Registro";
import Reportes from "./components/Reportes";
import Visitantes from "./components/Visitantes";
import Configuracion from "./components/Configuracion";

function App() {
  return (
    <div style={{ fontFamily: "sans-serif" }}>
      
      <nav
        style={{
          display: "flex",
          gap: "1rem",
          padding: "1rem",
          backgroundColor: "#1e293b",
          flexWrap: "wrap",
        }}
      >
        <Link style={linkStyle} to="/">Login</Link>
        <Link style={linkStyle} to="/usuarios">Usuarios</Link>
        <Link style={linkStyle} to="/productos">Productos</Link>
        <Link style={linkStyle} to="/registro">Registro</Link>
        <Link style={linkStyle} to="/reportes">Reportes</Link>
        <Link style={linkStyle} to="/visitantes">Visitantes</Link>
        <Link style={linkStyle} to="/configuracion">Configuración</Link>
      </nav>

      <Routes>
        <Route path="/" element={<Login />} />
        <Route path="/usuarios" element={<Usuarios />} />
        <Route path="/productos" element={<Productos />} />
        <Route path="/registro" element={<Registro />} />
        <Route path="/reportes" element={<Reportes />} />
        <Route path="/visitantes" element={<Visitantes />} />
        <Route path="/configuracion" element={<Configuracion />} />
      </Routes>
    </div>
  );
}

const linkStyle = {
  color: "white",
  textDecoration: "none",
  fontWeight: "bold",
  padding: "0.5rem 1rem",
  backgroundColor: "#334155",
  borderRadius: "8px",
};

export default App;