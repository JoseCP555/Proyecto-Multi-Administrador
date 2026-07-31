// Display & notification settings persisted in localStorage and applied globally

export interface AppSettings {
  notifAdmin: boolean
  notifRes: boolean
  notifVig: boolean
  brightness: number
  daltonismo: string | null
  tema: 'Claro' | 'Oscuro' | 'Siguiendo'
}

export const DEFAULT_SETTINGS: AppSettings = {
  notifAdmin: true,
  notifRes: true,
  notifVig: false,
  brightness: 70,
  daltonismo: null,
  tema: 'Siguiendo',
}

const SETTINGS_KEY = 'multiadmin_settings'

export function getSettings(): AppSettings {
  try {
    const raw = localStorage.getItem(SETTINGS_KEY)
    if (!raw) return { ...DEFAULT_SETTINGS }
    return { ...DEFAULT_SETTINGS, ...JSON.parse(raw) }
  } catch {
    return { ...DEFAULT_SETTINGS }
  }
}

export function saveSettings(settings: AppSettings) {
  localStorage.setItem(SETTINGS_KEY, JSON.stringify(settings))
  applySettings(settings)
}

function colorblindFilter(daltonismo: string | null): string {
  switch (daltonismo) {
    case 'Rojos-Verdes':
      // Protanopia/Deuteranopia-friendly approximation
      return 'grayscale(0.35) saturate(1.4) hue-rotate(-10deg)'
    case 'Azul-Amarillo':
      // Tritanopia-friendly approximation
      return 'grayscale(0.25) saturate(1.3) hue-rotate(20deg)'
    default:
      return ''
  }
}

export function resolveTheme(tema: AppSettings['tema']): 'Claro' | 'Oscuro' {
  if (tema === 'Siguiendo') {
    const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches
    return prefersDark ? 'Oscuro' : 'Claro'
  }
  return tema
}

export function applySettings(settings: AppSettings) {
  const root = document.documentElement

  // Theme
  const effectiveTheme = resolveTheme(settings.tema)
  if (effectiveTheme === 'Oscuro') {
    root.classList.add('theme-dark')
  } else {
    root.classList.remove('theme-dark')
  }

  // Brightness + colorblind filters combined
  const brightnessValue = Math.max(0.4, settings.brightness / 100)
  const cbFilter = colorblindFilter(settings.daltonismo)
  root.style.filter = cbFilter
    ? `brightness(${brightnessValue}) ${cbFilter}`
    : `brightness(${brightnessValue})`
}

export function initSettings() {
  applySettings(getSettings())
}
