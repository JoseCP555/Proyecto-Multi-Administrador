// Simple local authentication helper (mock backend using localStorage)

export interface User {
  name: string
  email: string
  password: string
  provider: 'email' | 'google' | 'apple'
}

const USERS_KEY = 'multiadmin_users'
const SESSION_KEY = 'multiadmin_session'

// Default admin account, always available
const DEFAULT_ADMIN: User = {
  name: 'Administrador',
  email: 'admin@gmail.com',
  password: '1234',
  provider: 'email',
}

// Accounts shown in the Google / Apple "choose an account" picker
export const GOOGLE_ACCOUNTS: { name: string; email: string; avatarColor: string }[] = [
  { name: 'Administrador', email: 'admin@gmail.com', avatarColor: '#2563eb' },
  { name: 'María Pérez', email: 'maria.perez@gmail.com', avatarColor: '#16a34a' },
  { name: 'Carlos Gómez', email: 'carlos.gomez@gmail.com', avatarColor: '#f59e0b' },
]

export const APPLE_ACCOUNTS: { name: string; email: string; avatarColor: string }[] = [
  { name: 'Administrador', email: 'admin@icloud.com', avatarColor: '#111827' },
  { name: 'María Pérez', email: 'maria.perez@icloud.com', avatarColor: '#6b7280' },
  { name: 'Carlos Gómez', email: 'carlos.gomez@icloud.com', avatarColor: '#374151' },
]

function getUsers(): User[] {
  try {
    const raw = localStorage.getItem(USERS_KEY)
    const users: User[] = raw ? JSON.parse(raw) : []

    // Ensure the default admin account always exists
    if (!users.some(u => u.email === DEFAULT_ADMIN.email)) {
      users.push(DEFAULT_ADMIN)
      saveUsers(users)
    }

    return users
  } catch {
    return [DEFAULT_ADMIN]
  }
}

function saveUsers(users: User[]) {
  localStorage.setItem(USERS_KEY, JSON.stringify(users))
}

export function registerUser(name: string, email: string, password: string): { ok: boolean; error?: string } {
  const users = getUsers()
  const normalizedEmail = email.trim().toLowerCase()

  if (users.some(u => u.email === normalizedEmail)) {
    return { ok: false, error: 'Ya existe una cuenta registrada con este correo.' }
  }

  users.push({ name, email: normalizedEmail, password, provider: 'email' })
  saveUsers(users)
  return { ok: true }
}

export function loginUser(email: string, password: string): { ok: boolean; error?: string; user?: User } {
  const users = getUsers()
  const normalizedEmail = email.trim().toLowerCase()
  const user = users.find(u => u.email === normalizedEmail)

  if (!user || user.password !== password) {
    return { ok: false, error: 'El correo o la contraseña son incorrectos.' }
  }

  setSession(user)
  return { ok: true, user }
}

export function loginWithAccount(provider: 'google' | 'apple', name: string, email: string): User {
  const users = getUsers()
  let user = users.find(u => u.email === email)

  if (!user) {
    user = { name, email, password: '', provider }
    users.push(user)
    saveUsers(users)
  }

  setSession(user)
  return user
}

export function setSession(user: User) {
  localStorage.setItem(SESSION_KEY, JSON.stringify({ name: user.name, email: user.email, provider: user.provider }))
}

export function getSession(): { name: string; email: string; provider: string } | null {
  try {
    const raw = localStorage.getItem(SESSION_KEY)
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

export function logout() {
  localStorage.removeItem(SESSION_KEY)
}

export function isAuthenticated(): boolean {
  return getSession() !== null
}
