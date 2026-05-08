import CardAccion from "./CardAction";

const Login = () => {

    const ingresar = () => {

        const usuario = (
            document.getElementById("usuario") as HTMLInputElement
        ).value;

        const contraseña = (
            document.getElementById("contraseña") as HTMLInputElement
        ).value;

        alert(`Usuario: ${usuario}\nContraseña: ${contraseña}`
        );

    };

    return (
        <main style={{
            flex: 1,
            padding: '1rem',
            display: 'flex',
            justifyContent:'center',
        }}>
        
        <div
        style={{
            border:'2px solid #afeba4',
            borderRadius:'4px',
            backgroundColor:'#77836e',
            padding:'1rem',
            width:'300px',
            textAlign:'center'
        }}>


        <h2>Login de usuario</h2>
        <p style={{ fontSize: '1rem', color:'#3a3b3a' }}>Ingrese sus datos</p>

        <input
        id="usuario"
        type="text"
        placeholder="usuario"

        style={{
        width:'250px',
        padding:'0.5rem',
        display:'block',
        margin:'0 auto 1rem auto'
        }}/>

        <input
        id="contraseña"
        type="password"
        placeholder="contraseña"

        style={{
        width:'250px',
        padding:'0.5rem',
        display:'block',
        margin:'0 auto 1rem auto'
        }}/>

        <CardAccion
        titulo=""
        descripcion=""
        textoBoton="Ingresar"
        onAccion={ingresar}
        />

        </div>
        </main>
    );
};


export default Login;