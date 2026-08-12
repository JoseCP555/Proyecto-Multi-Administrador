import DashboardLayout from '../components/DashboardLayout'
import './Finanzas.css'

const bancos = [
  'Nequi','Daviplata','Bancolombia','Banco de Bogotá','Davivienda',
  'BBVA','Banco de Occidente','Banco Popular','Banco AV Villas',
  'Banco Caja Social','Movii','Tpaga'
]

const pagos = ['Electricidad','Agua','Vigilancia','Aseo','Proveedores','Equipo']

const copropiedades = [
  'Conjunto Residencial Marensa',
  'Edificio Época II',
  'Conjunto Residencial Chamizo',
]

export default function Finanzas() {
  return (
    <DashboardLayout>
      <div className="fin-header">
        <button className="admin-mode-btn">Modo Administrador</button>
      </div>

      <div className="fin-cards">
        {copropiedades.map((copropiedad) => (
          <div key={copropiedad} className="fin-card">
            <h2>{copropiedad}</h2>

            <label>Pagos</label>
            <select>
              {pagos.map(p => <option key={p}>{p}</option>)}
            </select>

            <label>Bancos</label>
            <select multiple className="fin-banks">
              {bancos.map(b => <option key={b}>{b}</option>)}
            </select>
          </div>
        ))}
      </div>

      <div className="fin-info-section">
        <div className="fin-info-card">
          <h2>Copropiedades</h2>
          <div className="fin-list">
            <p>Conjunto Residencial Marensa</p>
            <p>Edificio Época II</p>
            <p>Parque Industrial Av. 98</p>
            <p>Edificio Miraflores</p>
            <p>Conjunto Residencial</p>
          </div>
        </div>

        <div className="fin-info-card large">
          <h2>Proveedores</h2>
          <div className="fin-list">
            <p>Aguas del Tequendama = <strong>$1.800.000</strong></p>
            <p>Servicios de Electricidad = <strong>$2.450.000</strong></p>
            <p>Internet Claro = <strong>$200.000</strong></p>
            <p>Movistar Teléfono = <strong>--------</strong></p>
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
