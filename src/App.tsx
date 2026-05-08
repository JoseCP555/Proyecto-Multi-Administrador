import { useState } from 'react';
import Usuarios from './components/Usuarios.tsx';
import Productos from './components/Productos.tsx';
import Login from './components/Login.tsx';
import Registro from './components/Registro.tsx';
import Reportes from './components/Reportes.tsx';

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
      </nav>

      <hr />

      <main>
        {pagina === 'usuarios' && <Usuarios />}
        {pagina === 'productos' && <Productos />}
        {pagina === 'login' && <Login />}
        {pagina === 'registro' && <Registro />}
        {pagina === 'reportes' && <Reportes />}
      </main>
    </div>
  );
}

export default App;