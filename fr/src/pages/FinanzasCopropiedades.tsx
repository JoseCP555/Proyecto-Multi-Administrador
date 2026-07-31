import DashboardLayout from '../components/DashboardLayout'
import './Finanzas.css'

export default function FinanzasCopropiedades() {
  return (
    <DashboardLayout>
      <div className="fin-header">
        <h2 style={{ fontSize: 22, fontWeight: 700, color: '#1e293b', marginBottom: 4 }}>Hola, Administrador</h2>
        <div style={{ display: 'flex', gap: 10, marginTop: 10 }}>
          <select style={{ padding: '8px 12px', borderRadius: 8, border: '1.5px solid #e2e8f0' }}>
            <option>Conjuntos</option>
          </select>
          <select style={{ padding: '8px 12px', borderRadius: 8, border: '1.5px solid #e2e8f0' }}>
            <option>Residencial Marensa</option>
          </select>
        </div>
      </div>

      <div className="fin-info-section">
        <div className="fin-info-card">
          <h2>Copropiedades</h2>
          <div className="fin-list">
            <p>Conjunto Residencial Marensa</p>
            <p>Edificio Época II</p>
            <p>Parque Industrial Av. 98</p>
            <p>Edificio Miraflores</p>
          </div>
        </div>
        <div className="fin-info-card large">
          <h2>Proveedores</h2>
          <div className="fin-list">
            <p>Aguas del Tequendama = <strong>$1.800.000</strong></p>
            <p>Servicios de Electricidad = <strong>$2.450.000</strong></p>
            <p>Internet Claro = <strong>$200.000</strong></p>
            <p>Movistar Teléfono = <strong>---</strong></p>
          </div>
        </div>
      </div>

      <div className="fin-vigilancia">
        <h2>Vigilancia</h2>
        <div className="fin-list">
          <p>Rebeca Rodríguez <span>6:00 AM – 12:00 PM</span></p>
          <p>Camilo Cifuentes <span>6:00 AM – 12:00 PM</span></p>
          <p>Juan Camilo Garzón <span>12:00 PM – 6:00 PM</span></p>
          <p>Tomas Rubio <span>12:00 PM – 6:00 PM</span></p>
        </div>
      </div>
    </DashboardLayout>
  )
}
