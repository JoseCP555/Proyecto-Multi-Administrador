import { useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import DashboardLayout from '../components/DashboardLayout'
import './Actas.css'

const docTabs = ['Actas','Reglamentos','Manuales','Contratos','Pólizas','Soporte','Evidencias']

interface Acta {
  id: number
  titulo: string
  numero: string
  descripcion: string
  fecha: string
  hora: string
  lugar: string
  archivo?: string
}

const initialActas: Acta[] = [
  { id:1, titulo:'Acta de Asamblea', numero:'ACTA No. 05', descripcion:'Asamblea General Ordinaria de Copropietarios', fecha:'15 de agosto de 2025', hora:'6:00 p.m', lugar:'Salón Comunal' },
  { id:2, titulo:'Acta de Consejo de Administración', numero:'ACTA No. 12', descripcion:'Reunión del Consejo de Administración', fecha:'20 de agosto de 2025', hora:'7:00 p.m', lugar:'Oficina de Administración' },
  { id:3, titulo:'Acta de reuniones de comités', numero:'ACTA No. 03', descripcion:'Reunión del Comité de Convivencia', fecha:'18 de agosto de 2025', hora:'6:30 p.m.', lugar:'Salón Comunal' },
]

function todayLabel() {
  const d = new Date()
  return d.toLocaleDateString('es-ES', { day: 'numeric', month: 'long', year: 'numeric' })
}

export default function Actas() {
  const navigate = useNavigate()
  const [activeTab, setActiveTab] = useState('Actas')
  const [actas, setActas] = useState<Acta[]>(initialActas)
  const [deleteMode, setDeleteMode] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleUploadClick = () => {
    fileInputRef.current?.click()
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    const nextNum = actas.length + 1
    const newActa: Acta = {
      id: actas.length ? Math.max(...actas.map(a => a.id)) + 1 : 1,
      titulo: file.name.replace(/\.[^/.]+$/, ''),
      numero: `ACTA No. ${String(nextNum).padStart(2, '0')}`,
      descripcion: 'Documento cargado por el administrador',
      fecha: todayLabel(),
      hora: new Date().toLocaleTimeString('es-ES', { hour: 'numeric', minute: '2-digit' }),
      lugar: 'Sin especificar',
      archivo: file.name,
    }

    setActas([...actas, newActa])
    e.target.value = ''
  }

  const handleDelete = (id: number) => {
    setActas(actas.filter(a => a.id !== id))
  }

  const toggleDeleteMode = () => {
    if (actas.length === 0 && !deleteMode) {
      alert('No hay actas para borrar')
      return
    }
    setDeleteMode(!deleteMode)
  }

  return (
    <DashboardLayout>
      <div className="actas-header">
        <h2>Hola, Administrador</h2>
        <button className="design-btn" onClick={() => navigate('/documentos')}>
          ← Documentos
        </button>
      </div>

      <div className="actas-layout">
        <div className="actas-menu">
          {docTabs.map(tab => (
            <button
              key={tab}
              className={`actas-tab ${activeTab === tab ? 'active' : ''}`}
              onClick={() => setActiveTab(tab)}
            >
              {tab}
            </button>
          ))}
        </div>

        <div className="actas-section">
          {activeTab !== 'Actas' && (
            <p className="actas-placeholder">No hay documentos en "{activeTab}" todavía.</p>
          )}

          {activeTab === 'Actas' && (
            <>
              <div className="actas-grid">
                {actas.map(acta => (
                  <div key={acta.id} className={`acta-card ${deleteMode ? 'deletable' : ''}`}>
                    {deleteMode && (
                      <button className="acta-remove" onClick={() => handleDelete(acta.id)} title="Eliminar este acta">
                        <i className="fa-solid fa-xmark"></i>
                      </button>
                    )}
                    <h3>{acta.titulo}</h3>
                    <p className="acta-num">{acta.numero}</p>
                    <p>{acta.descripcion}</p>
                    <p><i className="fa-regular fa-calendar"></i> {acta.fecha}</p>
                    <p><i className="fa-regular fa-clock"></i> {acta.hora}</p>
                    <p><i className="fa-solid fa-location-dot"></i> {acta.lugar}</p>
                    {acta.archivo && (
                      <p><i className="fa-solid fa-paperclip"></i> {acta.archivo}</p>
                    )}
                  </div>
                ))}
                {actas.length === 0 && (
                  <p className="actas-placeholder">No hay actas cargadas.</p>
                )}
              </div>

              <div className="actas-actions">
                <button className="upload-btn" onClick={handleUploadClick}>
                  <i className="fa-solid fa-upload"></i> Subir o Cargar
                </button>
                <input
                  ref={fileInputRef}
                  type="file"
                  style={{ display: 'none' }}
                  onChange={handleFileChange}
                />
                <button className={`delete-btn ${deleteMode ? 'active-delete' : ''}`} onClick={toggleDeleteMode}>
                  <i className="fa-solid fa-trash"></i> {deleteMode ? 'Listo' : 'Borrar un Acta'}
                </button>
              </div>
              {deleteMode && (
                <p className="delete-hint">Haz clic en la "✕" de la tarjeta del acta que deseas eliminar.</p>
              )}
            </>
          )}
        </div>
      </div>
    </DashboardLayout>
  )
}
