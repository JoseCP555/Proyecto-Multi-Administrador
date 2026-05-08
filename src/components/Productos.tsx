import CardAccion from "./CardAction";

const Productos = () => {

    const mostrarAccion = (accion: string) => {
      alert(`Se seleccionó: ${accion}`);
    };

    return (
      <aside
        style={{
            width: '260px',
            minHeight: '100vh',
            padding: '1rem',
            backgroundColor: '#77836e',
            display: 'flex',
            flexDirection: 'column',
            gap: '1rem'
            }}>

            <h2 style={{
                  color:'white',
                  textAlign:'center'
                }}>
                  
                Funciones Administrador
            </h2>

            <CardAccion
                titulo="Conjuntos"
                descripcion="Seleccionar conjuntos"
                textoBoton="Conjuntos"
                onAccion={() => mostrarAccion("Seleccionar Conjuntos")}
            />

            <CardAccion
                titulo="Horarios"
                descripcion="Consultar horarios"
                textoBoton="Horarios"
                onAccion={() => mostrarAccion("Consultar Horarios")}
            />

            <CardAccion
                titulo="Finanzas"
                descripcion="Consultar finanzas"
                textoBoton="Finanzas"
                onAccion={() => mostrarAccion("Consultar Finanzas")}
            />

            <CardAccion
                titulo="Proveedores"
                descripcion="Añadir proveedores"
                textoBoton="Proveedores"
                onAccion={() => mostrarAccion("Añadir Proveedores")}
            />

            <CardAccion
                titulo="Documentos"
                descripcion="Consultar documentos"
                textoBoton="Documentos"
                onAccion={() => mostrarAccion("Consultar Documentos")}
            />

            <CardAccion
                titulo="Mantenimientos"
                descripcion="Consultar mantenimientos"
                textoBoton="Mantenimientos"
                onAccion={() => mostrarAccion("Consultar Mantenimientos")}
            />

            <CardAccion
                titulo="Configuración"
                descripcion="Abrir configuración"
                textoBoton="Configuración"
                onAccion={() => mostrarAccion("Configuración")}
            />
    </aside>
  );
};

export default Productos;