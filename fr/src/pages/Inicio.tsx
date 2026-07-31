import { useState } from 'react'
import DashboardLayout from '../components/DashboardLayout'
import './Inicio.css'

interface Evento {
  id: number
  title: string
  date: string // YYYY-MM-DD
  type: 'fecha' | 'recordatorio' | 'evento'
}

const tipoIcono: Record<Evento['type'], string> = {
  fecha: 'fa-solid fa-flag',
  recordatorio: 'fa-solid fa-bell',
  evento: 'fa-solid fa-calendar-days',
}

const tipoColor: Record<Evento['type'], string> = {
  fecha: '#f59e0b',
  recordatorio: '#f97316',
  evento: '#2563eb',
}

const diasSemana = ['D', 'L', 'M', 'X', 'J', 'V', 'S']
const nombresMeses = [
  'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
  'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre',
]

function pad(n: number) {
  return n.toString().padStart(2, '0')
}

export default function Inicio() {
  const today = new Date()
  const [viewYear, setViewYear] = useState(today.getFullYear())
  const [viewMonth, setViewMonth] = useState(today.getMonth())
  const [selectedDate, setSelectedDate] = useState(
    `${today.getFullYear()}-${pad(today.getMonth() + 1)}-${pad(today.getDate())}`
  )

  const [eventos, setEventos] = useState<Evento[]>([
    { id: 1, title: 'Reunión de Consejo - Viernes 6:00 PM', date: `${today.getFullYear()}-${pad(today.getMonth() + 1)}-19`, type: 'fecha' },
    { id: 2, title: 'Revisión Tanques de agua - Martes', date: `${today.getFullYear()}-${pad(today.getMonth() + 1)}-16`, type: 'recordatorio' },
    { id: 3, title: 'Asamblea General de Copropietarios', date: `${today.getFullYear()}-${pad(today.getMonth() + 1)}-27`, type: 'evento' },
  ])

  const [showAddForm, setShowAddForm] = useState(false)
  const [newTitle, setNewTitle] = useState('')
  const [newType, setNewType] = useState<Evento['type']>('evento')

  const copropiedades = [
    'Conjunto Residencial Marensa',
    'Edificio Época II',
    'Parque Industrial Av. 98',
  ]

  const facturas = [
    { label: 'Aguas', value: 1800000 },
    { label: 'Electricidad', value: 2450000 },
    { label: 'Internet', value: 200000 },
  ]

  const formatMoney = (n: number) =>
    n.toLocaleString('es-CO') + '$'

  // Calendar grid calculation
  const firstDayOfMonth = new Date(viewYear, viewMonth, 1).getDay() // 0=Sunday
  const daysInMonth = new Date(viewYear, viewMonth + 1, 0).getDate()

  const cells: (number | null)[] = []
  for (let i = 0; i < firstDayOfMonth; i++) cells.push(null)
  for (let d = 1; d <= daysInMonth; d++) cells.push(d)
  while (cells.length % 7 !== 0) cells.push(null)

  const goPrevMonth = () => {
    if (viewMonth === 0) {
      setViewMonth(11)
      setViewYear(viewYear - 1)
    } else {
      setViewMonth(viewMonth - 1)
    }
  }

  const goNextMonth = () => {
    if (viewMonth === 11) {
      setViewMonth(0)
      setViewYear(viewYear + 1)
    } else {
      setViewMonth(viewMonth + 1)
    }
  }

  const dateKey = (day: number) => `${viewYear}-${pad(viewMonth + 1)}-${pad(day)}`

  const isToday = (day: number) =>
    day === today.getDate() && viewMonth === today.getMonth() && viewYear === today.getFullYear()

  const isSelected = (day: number) => dateKey(day) === selectedDate

  const hasEvent = (day: number) => eventos.some(e => e.date === dateKey(day))

  const handleAddEvent = () => {
    if (!newTitle.trim()) return
    const id = eventos.length ? Math.max(...eventos.map(e => e.id)) + 1 : 1
    setEventos([...eventos, { id, title: newTitle.trim(), date: selectedDate, type: newType }])
    setNewTitle('')
    setNewType('evento')
    setShowAddForm(false)
  }

  const handleRemoveEvent = (id: number) => {
    setEventos(eventos.filter(e => e.id !== id))
  }

  return (
    <DashboardLayout>
      <div className="inicio-header">
        <h2>Hola, Administrador</h2>
      </div>

      <div className="inicio-top-grid">
        <div className="inicio-card">
          <h3>Copropiedades</h3>
          <ul className="inicio-list">
            {copropiedades.map(c => (
              <li key={c}>{c}</li>
            ))}
          </ul>
        </div>

        <div className="inicio-card">
          <h3>Facturas por Pago</h3>
          <ul className="inicio-list">
            {facturas.map(f => (
              <li key={f.label}>{f.label} = {formatMoney(f.value)}</li>
            ))}
          </ul>
        </div>
      </div>

      <div className="inicio-card calendar-card">
        <h3><i className="fa-solid fa-calendar-days"></i> Calendario</h3>

        <div className="calendar-nav">
          <button className="cal-nav-btn" onClick={goPrevMonth}>
            <i className="fa-solid fa-chevron-left"></i>
          </button>
          <span className="cal-month-label">{nombresMeses[viewMonth]} {viewYear}</span>
          <button className="cal-nav-btn" onClick={goNextMonth}>
            <i className="fa-solid fa-chevron-right"></i>
          </button>
        </div>

        <table className="calendar-table">
          <thead>
            <tr>
              {diasSemana.map(d => <th key={d}>{d}</th>)}
            </tr>
          </thead>
          <tbody>
            {Array.from({ length: cells.length / 7 }).map((_, rowIdx) => (
              <tr key={rowIdx}>
                {cells.slice(rowIdx * 7, rowIdx * 7 + 7).map((day, i) => (
                  <td key={i}>
                    {day && (
                      <button
                        className={`cal-day ${isSelected(day) ? 'selected' : ''} ${isToday(day) ? 'today' : ''}`}
                        onClick={() => setSelectedDate(dateKey(day))}
                      >
                        {day}
                        {hasEvent(day) && <span className="cal-dot"></span>}
                      </button>
                    )}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="inicio-card eventos-card">
        <h3>Eventos</h3>

        <div className="eventos-list">
          {eventos
            .slice()
            .sort((a, b) => a.date.localeCompare(b.date))
            .map(ev => (
              <div className="evento-row" key={ev.id}>
                <div className="evento-info">
                  <span className="evento-title">{ev.title}</span>
                  <span className="evento-date">{ev.date}</span>
                </div>
                <div className="evento-actions">
                  <i
                    className={tipoIcono[ev.type]}
                    style={{ color: tipoColor[ev.type] }}
                    title={ev.type}
                  ></i>
                  <button className="evento-remove" onClick={() => handleRemoveEvent(ev.id)} title="Eliminar">
                    <i className="fa-solid fa-xmark"></i>
                  </button>
                </div>
              </div>
            ))}
          {eventos.length === 0 && (
            <p className="evento-empty">No hay eventos programados</p>
          )}
        </div>

        {showAddForm && (
          <div className="evento-form">
            <input
              type="text"
              placeholder="Título del evento"
              value={newTitle}
              onChange={e => setNewTitle(e.target.value)}
            />
            <select value={newType} onChange={e => setNewType(e.target.value as Evento['type'])}>
              <option value="evento">Evento</option>
              <option value="fecha">Fecha importante</option>
              <option value="recordatorio">Recordatorio</option>
            </select>
            <span className="evento-form-date">Fecha: {selectedDate}</span>
          </div>
        )}

        <div className="eventos-buttons">
          {!showAddForm ? (
            <button className="btn-primary" onClick={() => setShowAddForm(true)}>
              Añadir Eventos
            </button>
          ) : (
            <>
              <button className="btn-primary" onClick={handleAddEvent}>
                Guardar
              </button>
              <button className="btn-secondary" onClick={() => setShowAddForm(false)}>
                Cancelar
              </button>
            </>
          )}
          {!showAddForm && (
            <button
              className="btn-secondary"
              onClick={() => eventos.length && handleRemoveEvent(eventos[eventos.length - 1].id)}
              disabled={eventos.length === 0}
            >
              Quitar Eventos
            </button>
          )}
        </div>
      </div>
    </DashboardLayout>
  )
}
