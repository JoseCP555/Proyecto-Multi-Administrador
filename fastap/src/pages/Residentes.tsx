import { useState } from 'react'
import DashboardLayout from '../components/DashboardLayout'
import './Residentes.css'

interface Residente {
  id: number
  nombre: string
  conjunto: string
}

const conjuntos = ['Marensa', 'Época II', 'Miraflores', 'Chamizo']

const initialResidentes: Residente[] = [
  { id: 1, nombre: 'Juan Pérez', conjunto: 'Marensa' },
  { id: 2, nombre: 'María Gómez', conjunto: 'Época II' },
  { id: 3, nombre: 'Mauricio Gálazar', conjunto: 'Miraflores' },
  { id: 4, nombre: 'Camila Rodríguez', conjunto: 'Chamizo' },
]

let nextId = 5

export default function Residentes() {
  const [residentes, setResidentes] = useState<Residente[]>(initialResidentes)
  const [nombre, setNombre] = useState('')
  const [conjunto, setConjunto] = useState(conjuntos[0])
  const [seleccionado, setSeleccionado] = useState<number | null>(null)
  const [search, setSearch] = useState('')
  const [mensaje, setMensaje] = useState('')

  const mostrarMensaje = (txt: string) => {
    setMensaje(txt)
    setTimeout(() => setMensaje(''), 2500)
  }

  const seleccionarResidente = (r: Residente) => {
    setSeleccionado(r.id)
    setNombre(r.nombre)
    setConjunto(r.conjunto)
  }

  const agregar = () => {
    if (!nombre.trim()) { mostrarMensaje('Escribe un nombre'); return }
    setResidentes([...residentes, { id: nextId++, nombre: nombre.trim(), conjunto }])
    setNombre('')
    mostrarMensaje('Residente agregado correctamente')
  }

  const editar = () => {
    if (!seleccionado) { mostrarMensaje('Selecciona un residente'); return }
    setResidentes(residentes.map(r => r.id === seleccionado ? { ...r, nombre, conjunto } : r))
    mostrarMensaje('Datos actualizados')
  }

  const eliminar = () => {
    if (!seleccionado) { mostrarMensaje('Selecciona un residente'); return }
    if (!confirm('¿Seguro que deseas eliminar?')) return
    setResidentes(residentes.filter(r => r.id !== seleccionado))
    setSeleccionado(null)
    setNombre('')
    mostrarMensaje('Residente eliminado')
  }

  const filtrados = residentes.filter(r =>
    r.nombre.toLowerCase().includes(search.toLowerCase()) ||
    r.conjunto.toLowerCase().includes(search.toLowerCase())
  )

  const selected = residentes.find(r => r.id === seleccionado)

  return (
    <DashboardLayout onSearch={setSearch}>
      <div className="res-header">
        <div>
          <h2>Hola, Administrador</h2>
          <p className="res-sub">Gestión de Residentes</p>
        </div>
        <div className="res-selects">
          <select><option>Conjuntos</option></select>
          <select><option>Residencial Marensa</option></select>
        </div>
      </div>

      <div className="res-form">
        <input
          type="text"
          placeholder="Nombre del residente"
          value={nombre}
          onChange={e => setNombre(e.target.value)}
        />
        <select value={conjunto} onChange={e => setConjunto(e.target.value)}>
          {conjuntos.map(c => <option key={c}>{c}</option>)}
        </select>
        <button className="btn-add" onClick={agregar}>Agregar</button>
        <button className="btn-edit" onClick={editar}>Editar</button>
        <button className="btn-del" onClick={eliminar}>Eliminar</button>
      </div>

      {mensaje && <div className="res-mensaje">{mensaje}</div>}

      <div className="res-content">
        <div className="res-box">
          <h3>Lista de Residentes</h3>
          <ul className="res-list">
            {filtrados.map(r => (
              <li
                key={r.id}
                className={`res-item ${r.id === seleccionado ? 'selected' : ''}`}
                onClick={() => seleccionarResidente(r)}
              >
                <span className="res-avatar">{r.nombre[0]}</span>
                <span>{r.nombre}</span>
                <span className="res-tag">{r.conjunto}</span>
              </li>
            ))}
            {filtrados.length === 0 && (
              <li className="res-empty">No hay residentes que coincidan</li>
            )}
          </ul>
        </div>

        <div className="res-box">
          <h3>Detalle del Residente</h3>
          {selected ? (
            <div className="res-detalle">
              <div className="res-avatar-big">{selected.nombre[0]}</div>
              <p><strong>Nombre:</strong> {selected.nombre}</p>
              <p><strong>Conjunto:</strong> {selected.conjunto}</p>

              <div className="service-cards">
                {[
                  { icon: 'fa-lightbulb', label: 'Luz', status: 'Al día', ok: true },
                  { icon: 'fa-droplet', label: 'Agua', status: 'Debe $45.000', ok: false },
                  { icon: 'fa-house', label: 'Alquiler', status: 'Al día', ok: true },
                  { icon: 'fa-fire', label: 'Gas', status: 'Al día', ok: true },
                ].map(s => (
                  <div key={s.label} className="service-card">
                    <div className="s-icon"><i className={`fa-solid ${s.icon}`}></i></div>
                    <div>
                      <strong>{s.label}</strong>
                      <span className={s.ok ? 'ok' : 'err'}>{s.status}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <p className="res-placeholder">Selecciona un residente para ver detalles</p>
          )}
        </div>
      </div>
    </DashboardLayout>
  )
}
