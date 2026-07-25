import { useEffect, useState } from 'react'
import DashboardLayout from '../components/DashboardLayout'
import { getSettings, saveSettings, DEFAULT_SETTINGS, AppSettings } from '../settings'
import './Configuracion.css'

export default function Configuracion() {
  const [settings, setSettings] = useState<AppSettings>(getSettings())
  const [savedMsg, setSavedMsg] = useState('')

  // Apply and persist settings whenever they change (live preview)
  useEffect(() => {
    saveSettings(settings)
  }, [settings])

  const update = (partial: Partial<AppSettings>) => {
    setSettings(prev => ({ ...prev, ...partial }))
  }

  const reset = () => {
    setSettings({ ...DEFAULT_SETTINGS })
    setSavedMsg('Configuración restablecida')
    setTimeout(() => setSavedMsg(''), 2000)
  }

  const CheckOption = ({ label, checked, onChange }: { label: string, checked: boolean, onChange: () => void }) => (
    <label className="check-label">
      <input type="checkbox" checked={checked} onChange={onChange} />
      {label}
    </label>
  )

  return (
    <DashboardLayout>
      <div className="config-header">
        <div>
          <h2>Hola, Administrador</h2>
          <p className="config-sub">Configuración del sistema</p>
        </div>
        <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
          <select
            style={{ padding: '8px 12px', borderRadius: 8, border: '1.5px solid #e2e8f0' }}
            onChange={e => {
              if (e.target.value === 'exportar') {
                alert('Exportando configuración:\n' + JSON.stringify(settings, null, 2))
              } else if (e.target.value === 'restaurar') {
                reset()
              }
              e.target.value = ''
            }}
          >
            <option value="">Ajustes</option>
            <option value="exportar">Exportar configuración</option>
            <option value="restaurar">Restaurar valores predeterminados</option>
          </select>
          <button
            className="design-btn"
            onClick={() => alert('El diseño de página se aplicará según el tema y brillo seleccionados.')}
          >
            Diseño de Página
          </button>
        </div>
      </div>

      <div className="config-cards">
        {/* Notificaciones */}
        <div className="config-card">
          <h3><i className="fa-solid fa-bell"></i> Notificaciones</h3>

          <div className="option-group">
            <p>Activar Notificaciones</p>
            <CheckOption label="Sí" checked={settings.notifAdmin} onChange={() => update({ notifAdmin: true })} />
            <CheckOption label="No" checked={!settings.notifAdmin} onChange={() => update({ notifAdmin: false })} />
          </div>

          <div className="option-group">
            <p>Activar Notificaciones a los residentes</p>
            <CheckOption label="Sí" checked={settings.notifRes} onChange={() => update({ notifRes: true })} />
            <CheckOption label="No" checked={!settings.notifRes} onChange={() => update({ notifRes: false })} />
          </div>

          <div className="option-group">
            <p>Activar Notificaciones de Vigilancia</p>
            <CheckOption label="Sí" checked={settings.notifVig} onChange={() => update({ notifVig: true })} />
            <CheckOption label="No" checked={!settings.notifVig} onChange={() => update({ notifVig: false })} />
          </div>
        </div>

        {/* Pantalla */}
        <div className="config-card">
          <h3><i className="fa-solid fa-display"></i> Pantalla</h3>

          <div className="brightness-group">
            <label>Nivel de Brillo: {settings.brightness}%</label>
            <input
              type="range"
              min={40}
              max={100}
              value={settings.brightness}
              onChange={e => update({ brightness: Number(e.target.value) })}
            />
          </div>

          <div className="option-group">
            <p>Ajustes para Daltonismo</p>
            {['Rojos-Verdes','Azul-Amarillo','Ninguno'].map(opt => (
              <label key={opt} className="check-label">
                <input
                  type="checkbox"
                  checked={opt === 'Ninguno' ? settings.daltonismo === null : settings.daltonismo === opt}
                  onChange={() => update({ daltonismo: opt === 'Ninguno' ? null : opt })}
                />
                {opt}
              </label>
            ))}
          </div>

          <div className="option-group">
            <p>Tema</p>
            {['Claro','Oscuro','Siguiendo'].map(opt => (
              <label key={opt} className="check-label">
                <input
                  type="radio"
                  name="tema"
                  checked={settings.tema === opt}
                  onChange={() => update({ tema: opt as AppSettings['tema'] })}
                />
                {opt}
              </label>
            ))}
          </div>
        </div>
      </div>

      <div className="reset-container">
        <button className="reset-btn" onClick={reset}>
          <i className="fa-solid fa-rotate-left"></i> Restablecimiento
        </button>
      </div>

      {savedMsg && <p className="config-saved-msg">{savedMsg}</p>}
    </DashboardLayout>
  )
}
