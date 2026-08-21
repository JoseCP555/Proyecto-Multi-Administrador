// Manejo de sesión del usuario autenticado.
// La autenticación real la realiza el backend FastAPI mediante JWT.

export interface SessionUser {
  id?: number
  nombre?: string
  name?: string
  correo?: string
  email?: string
  rol?: number
  id_rol?: number
  id_copropiedad?: number | null
  provider?: 'email' | 'google' | 'apple'
}

export interface AccountOption {
  name: string
  email: string
  avatarColor: string
}

const SESSION_KEY = 'multiadmin_session'
const USER_KEY = 'usuario'
const TOKEN_KEY = 'access_token'

// Estas cuentas todavía son solo opciones visuales del selector.
// No representan autenticación real con Google o Apple.
export const GOOGLE_ACCOUNTS: AccountOption[] = [
  {
    name: 'Administrador',
    email: 'admin@gmail.com',
    avatarColor: '#2563eb',
  },
  {
    name: 'María Pérez',
    email: 'maria.perez@gmail.com',
    avatarColor: '#16a34a',
  },
  {
    name: 'Carlos Gómez',
    email: 'carlos.gomez@gmail.com',
    avatarColor: '#f59e0b',
  },
]

export const APPLE_ACCOUNTS: AccountOption[] = [
  {
    name: 'Administrador',
    email: 'admin@icloud.com',
    avatarColor: '#111827',
  },
  {
    name: 'María Pérez',
    email: 'maria.perez@icloud.com',
    avatarColor: '#6b7280',
  },
  {
    name: 'Carlos Gómez',
    email: 'carlos.gomez@icloud.com',
    avatarColor: '#374151',
  },
]

export function saveAuthSession(
  usuario: SessionUser,
  token: string
) {
  localStorage.setItem(USER_KEY, JSON.stringify(usuario))
  localStorage.setItem(TOKEN_KEY, token)

  setSession({
    name: usuario.nombre || usuario.name || '',
    email: usuario.correo || usuario.email || '',
    provider: 'email',
  })
}

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY)
}

export function getCurrentUser(): SessionUser | null {
  try {
    const raw = localStorage.getItem(USER_KEY)

    if (!raw) {
      return null
    }

    return JSON.parse(raw) as SessionUser
  } catch {
    return null
  }
}

export function setSession(user: {
  name: string
  email: string
  provider: 'email' | 'google' | 'apple'
}) {
  localStorage.setItem(SESSION_KEY, JSON.stringify(user))
}

export function getSession(): {
  name: string
  email: string
  provider: string
} | null {
  try {
    const raw = localStorage.getItem(SESSION_KEY)

    if (!raw) {
      return null
    }

    return JSON.parse(raw)
  } catch {
    return null
  }
}

export function logout() {
  localStorage.removeItem(USER_KEY)
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(SESSION_KEY)
}

export function isAuthenticated(): boolean {
  const usuario = localStorage.getItem(USER_KEY)
  const token = localStorage.getItem(TOKEN_KEY)

  return Boolean(usuario && token)
}

// Esta función se conserva solo para que el selector actual no genere
// errores de compilación. Google y Apple todavía no están conectados
// al backend y no deben considerarse autenticación real.
export function loginWithAccount(
  provider: 'google' | 'apple',
  name: string,
  email: string
) {
  setSession({
    name,
    email,
    provider,
  })
}
