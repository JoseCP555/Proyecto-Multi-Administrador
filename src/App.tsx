import { useState } from 'react';
import Usuarios from './components/Usuarios copy.tsx';
import Productos from './components/Productos copy.tsx';
import Login from './components/Login copy.tsx';
import Registro from './components/Registro copy.tsx';
import Reportes from './components/Reportes copy.tsx';
import Visitantes from './components/Visitantes copy.tsx';
import Configuracion from './components/Configuracion.tsx';
import CoreAdmin from './Components/CoreAdmin .tsx';
function App() {
  const [pagina, setPagina] = useState<string>('usuarios');

  return (
    <div style={{ fontFamily: 'sans-serif', padding: '20px' }}>
      <nav style={{ marginBottom: '20px' }}>
        <button onClick={() => setPagina('usuarios')}>Ver Usuarios</button>
        <button onClick={() => setPagina('productos')} style={{ marginLeft: '10px' }}>Ver Productos</button>
        <button onClick={() => setPagina('login')} style={{ marginLeft: '10px' }}>Ver Login</button>
        <button onClick={() => setPagina('registro')} style={{ marginLeft: '10px' }}>Ver Registro</button>
        <button onClick={() => setPagina('reportes')} style={{ marginLeft: '10px' }}>Ver Reportes</button>
        <button onClick={() => setPagina('visitantes')} style={{ marginLeft: '10px' }}>Ver visitantes</button>
        <button onClick={() => setPagina('configuracion')} style={{ marginLeft: '10px' }}>Configuración</button>
        <button onClick={() => setPagina('CoreAdmin ')} style={{ marginLeft: '10px' }}>Ver CoreAdmin </button>

      </nav>

      <hr />

      <main>
        {pagina === 'usuarios' && <Usuarios />}
        {pagina === 'productos' && <Productos />}
        {pagina === 'login' && <Login />}
        {pagina === 'registro' && <Registro />}
        {pagina === 'reportes' && <Reportes />}
        {pagina === 'visitantes' && <Visitantes />}
        {pagina === 'configuracion' && <Configuracion />}
        {pagina === 'CoreAdmin ' && <CoreAdmin  />}

      </main>
    </div>
  );
}

export default App;