import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import DashboardLayout from '../components/DashboardLayout'
import './Documentos.css'

const docButtons = ['Copropiedad','Actas','Reglamentos','Manuales','Contratos','Pólizas','Soporte','Evidencias']
const copropiedades = [
  'Conjunto Residencial Marensa',
  'Edificio Época',
  'Conjunto Lugano',
  'Conjunto Residencial Salvator',
]

export default function Documentos() {
  const navigate = useNavigate()
  const [activeDoc, setActiveDoc] = useState('Copropiedad')
  const [selectedCopro, setSelectedCopro] = useState<string[]>([])

  const toggleCopro = (c: string) => {
    setSelectedCopro(prev =>
      prev.includes(c) ? prev.filter(x => x !== c) : [...prev, c]
    )
  }

  return (
    <DashboardLayout>
      <div className="doc-header">
        <h2>Hola, Administrador</h2>
        <button className="design-btn" onClick={() => navigate('/documentos/actas')}>
          Diseño de Página
        </button>
      </div>

      <div className="doc-layout">
        <div className="doc-copro-section">
          <h3>Copropiedades</h3>
          <div className="copro-list">
            {copropiedades.map(c => (
              <div
                key={c}
                className={`copro-item ${selectedCopro.includes(c) ? 'selected' : ''}`}
                onClick={() => toggleCopro(c)}
              >
                {c}
              </div>
            ))}
          </div>
        </div>

        <div className="doc-grid">
          {docButtons.map(btn => (
            <button
              key={btn}
              className={`doc-type-btn ${activeDoc === btn ? 'active' : ''}`}
              onClick={() => {
                setActiveDoc(btn)
                if (btn === 'Actas') navigate('/documentos/actas')
              }}
            >
              {btn}
            </button>
          ))}
        </div>
      </div>
    </DashboardLayout>
  )
}
