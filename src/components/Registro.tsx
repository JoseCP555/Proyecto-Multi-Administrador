import CardAccion from "./CardAction";

const Registro = () => {

    const registrar = () => {

        const nombre = (
            document.getElementById("nombre") as HTMLInputElement
        ).value;

        const correo = (
            document.getElementById("correo") as HTMLInputElement
        ).value;

        const contraseña = (
            document.getElementById("contraseña") as HTMLInputElement
        ).value;

        alert(`Nombre: ${nombre}\nCorreo: ${correo}\nContraseña: ${contraseña}`);
    };

    return (
        <main
            style={{
                minHeight: '100vh',
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center'
            }}>

            <div
                style={{
                    border: '2px solid #afeba4',
                    borderRadius: '4px',
                    backgroundColor: '#77836e',
                    padding: '2rem',
                    width: '350px',
                    textAlign: 'center'
                }}>

                <h2>Registro de Usuarios</h2>
                <p style={{ fontSize: '1rem', color:'#3a3b3a' }}>Crear nueva cuenta</p>

                <input
                    id="nombre"
                    type="text"
                    placeholder="Nombre"
                    style={{
                        width: '250px',
                        padding: '0.5rem',
                        display: 'block',
                        margin: '0 auto 1rem auto'
                    }}/>

                <input
                    id="correo"
                    type="text"
                    placeholder="Correo"
                    style={{
                        width: '250px',
                        padding: '0.5rem',
                        display: 'block',
                        margin: '0 auto 1rem auto'
                    }}/>

                <input
                    id="contraseña"
                    type="password"
                    placeholder="Contraseña"
                    style={{
                        width: '250px',
                        padding: '0.5rem',
                        display: 'block',
                        margin: '0 auto 1rem auto'
                    }}/>

                <CardAccion
                    titulo=""
                    descripcion=""
                    textoBoton="Registrar"
                    onAccion={registrar}
                />
            </div>
        </main>
    );
};

export default Registro;