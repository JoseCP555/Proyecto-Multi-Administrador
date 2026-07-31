import { useState } from 'react'
import DashboardLayout from '../components/DashboardLayout'
import './Reportes.css'

const reportTabs = ['Actas','Reglamentos','Manuales','Contratos','Pólizas','Soporte','Evidencias']

const reportCards = [
  { titulo:'Acta de Asamblea', numero:'ACTA No. 05', descripcion:'Asamblea General Ordinaria de Copropietarios', fecha:'15 de agosto de 2025', hora:'6:00 p.m', lugar:'Salón Comunal' },
  { titulo:'Acta de Consejo de Administración', numero:'ACTA No. 12', descripcion:'Reunión del Consejo de Administración', fecha:'20 de agosto de 2025', hora:'7:00 p.m', lugar:'Oficina de Administración' },
  { titulo:'Acta de reuniones de comités', numero:'ACTA No. 03', descripcion:'Reunión del Comité de Convivencia', fecha:'18 de agosto de 2025', hora:'6:30 p.m.', lugar:'Salón Comunal' },
]

export default function Reportes() {
  const [activeTab, setActiveTab] = useState('Actas')

  return (
    <DashboardLayout>
      <div className="rep-header">
        <div>
          <h2>Hola, Administrador</h2>
          <p className="rep-sub">Reportes y documentos</p>
        </div>
        <div className="rep-filters">
          <select><option>Copropiedad</option></select>
          <select><option>Conjuntos</option></select>
          <button className="design-btn">Diseño de Página</button>
        </div>
      </div>

      <div className="rep-layout">
        <div className="rep-menu">
          {reportTabs.map(tab => (
            <button
              key={tab}
              className={`rep-tab ${activeTab === tab ? 'active' : ''}`}
              onClick={() => setActiveTab(tab)}
            >
              {tab}
            </button>
          ))}
        </div>

        <div className="rep-content">
          <div className="rep-grid">
            {reportCards.map((c, i) => (
              <div key={i} className="rep-card">
                <h3>{c.titulo}</h3>
                <p className="rep-num">{c.numero}</p>
                <p>{c.descripcion}</p>
                <p><i className="fa-regular fa-calendar"></i> {c.fecha}</p>
                <p><i className="fa-regular fa-clock"></i> {c.hora}</p>
                <p><i className="fa-solid fa-location-dot"></i> {c.lugar}</p>
              </div>
            ))}
          </div>

          <div className="rep-empty-grid">
            {[0,1,2].map(i => (
              <div key={i} className="rep-empty">No hay información disponible</div>
            ))}
          </div>
        </div>
      </div>
    </DashboardLayout>
  )
}
