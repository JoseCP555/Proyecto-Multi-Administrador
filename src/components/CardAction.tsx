interface CardAccionProps {
  titulo: string;
  descripcion: string;
  textoBoton?: string;
  onAccion: (info: string) => void;
}
 
function CardAccion({
  titulo,
  textoBoton = "Ejecutar",
  onAccion,
}: CardAccionProps) {

  return (
      <button
        onClick={() => onAccion(titulo || textoBoton)}
        style={{
          display: 'block',
          margin: '0 auto',
          width: '70%',
          padding: '1.2rem 1rem',
          backgroundColor: '#4e7750',
          color: 'white',
          border: 'none',
          borderRadius: '6px',
          cursor: 'pointer',
          fontSize: '0.85rem',
          fontWeight: 'bold',
          whiteSpace:'normal',
          textAlign:'center'
        }}
      >
        {textoBoton}
      </button>
  );
}
 
export default CardAccion;