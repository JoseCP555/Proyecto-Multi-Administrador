const Usuarios = () => {
    return (
    <main style={{ flex: 1, padding: '2rem', backgroundColor:'#77836e'}}>
      <h2>Bienvenido Administrador</h2>
      <p style={{ fontSize: '1rem', color:'#0b0c0b' }}>¿Que hay para hacer hoy?</p>
      

    <div style={{ display: 'flex', flexDirection: 'row', gap: '1rem', marginTop: '1rem' }}>


    <div style={{ border: '2px solid #4e7750', padding: '1rem', borderRadius: '4px', width: '200px', minHeight: '150px', backgroundColor:'#759957' }}>
        <h3 style={{ marginBottom: '0.5rem', fontSize: '1rem', color:'#0b0c0b' }}>─ Horarios ─</h3>
        <p style={{ fontSize: '0.85rem', color:'#0b0c0b' }}>Lunes 1:00pm - 6:00 pm</p>
        <p style={{ fontSize: '0.85rem', color:'#0b0c0b' }}>Conjunto La Esperanza</p>
    </div>
    <div style={{ border: '2px solid #4e7750', padding: '1rem', borderRadius: '4px', width: '200px', minHeight: '150px', backgroundColor:'#759957' }}>
        <h3 style={{ marginBottom: '0.5rem', fontSize: '1rem', color:'#0b0c0b' }}>─ Mantenimientos ─</h3>
        <p style={{ fontSize: '0.85rem', color:'#0b0c0b'}}>Ninguno</p>
    </div>
    <div style={{ border: '2px solid #4e7750', padding: '1rem', borderRadius: '4px', width: '200px', minHeight: '150px', backgroundColor:'#759957' }}>
        <h3 style={{ marginBottom: '0.5rem', fontSize: '1rem', color:'#0b0c0b' }}>─ Deudas ─</h3>
        <p style={{ fontSize: '0.85rem', color:'#0b0c0b' }}>Mario Castañeda - Apat 101</p>
        <p style={{ fontSize: '0.85rem', color:'#0b0c0b' }}>Administración</p>
    </div>
    <div style={{ border: '2px solid #4e7750', padding: '1rem', borderRadius: '4px', width: '200px', minHeight: '150px', backgroundColor:'#759957'  }}>
        <h3 style={{ marginBottom: '0.5rem', fontSize: '1rem', color:'#0b0c0b' }}>─ Reuniones ─</h3>
        <p style={{ fontSize: '0.85rem', color:'#0b0c0b' }}>Viernes 8:00am - 12:00 pm</p>
        <p style={{ fontSize: '0.85rem', color:'#0b0c0b' }}>Asamblea Extraordinaria</p>
         </div>
    </div>
    </main>
  );
};

export default Usuarios;