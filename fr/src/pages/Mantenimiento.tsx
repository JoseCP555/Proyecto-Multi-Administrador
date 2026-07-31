import { useState } from 'react'
import DashboardLayout from '../components/DashboardLayout'
import './Mantenimiento.css'

interface Tarea {
  id: number
  texto: string
}

interface CardProps {
  title: string
  items: Tarea[]
  setItems: React.Dispatch<React.SetStateAction<Tarea[]>>
  label: string
  color: string
}

function MantCard({ title, items, setItems, label, color }: CardProps) {
  const [inputVisible, setInputVisible] = useState(false)
  const [inputValue, setInputValue] = useState('')

  const handleAgregar = () => {
    if (inputValue.trim()) {
      setItems(prev => [...prev, { id: Date.now(), texto: inputValue.trim() }])
      setInputValue('')
      setInputVisible(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') handleAgregar()
    if (e.key === 'Escape') { setInputVisible(false); setInputValue('') }
  }

  return (
    <div className="mant-card">
      <div className="mant-card-header" style={{ borderLeftColor: color }}>
        <h2>{title}</h2>
      </div>

      <ul className="mant-list">
        {items.map(t => (
          <li key={t.id}>
            <span className="mant-dot" style={{ background: color }}></span>
            <span className="mant-text">{t.texto}</span>
            <button
              className="mant-remove"
              onClick={() => setItems(prev => prev.filter(i => i.id !== t.id))}
              title="Eliminar"
            >
              ×
            </button>
          </li>
        ))}
      </ul>

      {inputVisible && (
        <div className="mant-input-row">
          <input
            autoFocus
            type="text"
            placeholder={`Nueva ${label}...`}
            value={inputValue}
            onChange={e => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            className="mant-input"
          />
          <button
            className="mant-confirm-btn"
            style={{ background: color }}
            onClick={handleAgregar}
          >
            ✓
          </button>
          <button
            className="mant-cancel-btn"
            onClick={() => { setInputVisible(false); setInputValue('') }}
          >
            ✕
          </button>
        </div>
      )}

      {!inputVisible && (
        <button
          className="mant-btn"
          style={{ background: color }}
          onClick={() => setInputVisible(true)}
        >
          + Incluir {label}
        </button>
      )}
    </div>
  )
}

export default function Mantenimiento() {
  const [aseo, setAseo] = useState<Tarea[]>([
    { id: 1, texto: 'Limpieza de las escaleras del 4 piso' },
    { id: 2, texto: 'Limpieza ventana del 3 piso' },
    { id: 3, texto: 'Limpieza de las puertas de todos los pisos' },
    { id: 4, texto: 'Limpieza de las barandas de seguridad de cada piso' },
  ])
  const [reparaciones, setReparaciones] = useState<Tarea[]>([
    { id: 1, texto: 'Cortar electricidad de las luces exteriores' },
    { id: 2, texto: 'Revisión del sistema de acueducto' },
    { id: 3, texto: 'Comprobar sistema de luces del parqueadero' },
    { id: 4, texto: 'Revisión de las puertas automáticas del edificio 3' },
  ])
  const [informes, setInformes] = useState<Tarea[]>([
    { id: 1, texto: 'Daño en un baño del piso 1' },
    { id: 2, texto: 'Sistema de emergencia no funciona' },
    { id: 3, texto: 'Luces de los pasillos fallan' },
  ])

  return (
    <DashboardLayout>
      <div className="mant-header">
        <h2>Hola, Administrador</h2>
        <button className="admin-mode-btn">
          Modo Administrador
        </button>
      </div>

      <div className="mant-grid">
        <MantCard
          title="Aseo de cada piso del departamento"
          items={aseo}
          setItems={setAseo}
          label="tarea de aseo"
          color="#2563eb"
        />
        <MantCard
          title="Reparaciones de emergencia"
          items={reparaciones}
          setItems={setReparaciones}
          label="revisión o reparación"
          color="#f59e0b"
        />
        <MantCard
          title="Informe de daños o emergencias"
          items={informes}
          setItems={setInformes}
          label="informe"
          color="#ef4444"
        />
      </div>
    </DashboardLayout>
  )
}
