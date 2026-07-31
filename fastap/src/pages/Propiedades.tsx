import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import DashboardLayout from '../components/DashboardLayout'
import './Propiedades.css'

const cardsData = [
  { title: 'Horario', content: 'Lunes\nEdificio Época 7:00 AM - 12:00 PM' },
  { title: 'Eventos', content: 'No hay Eventos' },
  { title: 'Programa', content: 'No hay ningún Programa' },
  { title: 'Reuniones', content: 'Reunión de Consejo\n6:00 PM - Viernes' },
  { title: 'Mantenimiento', content: 'Revisión Tanques de agua\nMartes' },
]

export default function Propiedades() {
  const navigate = useNavigate()
  const [search, setSearch] = useState('')

  const filtered = cardsData.filter(c =>
    c.title.toLowerCase().includes(search.toLowerCase()) ||
    c.content.toLowerCase().includes(search.toLowerCase())
  )

  return (
    <DashboardLayout onSearch={setSearch}>
      <div className="propiedades-header">
        <div>
          <h2>Hola, Administrador</h2>
          <p className="sub">Panel principal de propiedades</p>
        </div>
        <div className="prop-filters">
          <select>
            <option>Copropiedad</option>
            <option>Edificios</option>
            <option>Apartamentos</option>
          </select>
          <select>
            <option>Conjuntos</option>
            <option>Torres</option>
            <option>Casas</option>
          </select>
          <button
            className="design-btn"
            onClick={() => navigate('/residentes')}
          >
            Diseño de Página
          </button>
        </div>
      </div>

      <div className="prop-cards">
        {filtered.map((card) => (
          <div key={card.title} className="prop-card">
            <h3>{card.title}</h3>
            <p>{card.content}</p>
          </div>
        ))}
        {filtered.length === 0 && (
          <p className="no-results">No se encontraron resultados</p>
        )}
      </div>
    </DashboardLayout>
  )
}
