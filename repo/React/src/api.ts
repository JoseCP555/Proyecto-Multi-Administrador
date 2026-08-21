import { getToken, logout } from './auth'

export const API_URL =
  import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'

export async function apiFetch(
  endpoint: string,
  options: RequestInit = {}
): Promise<Response> {
  const token = getToken()
  const headers = new Headers(options.headers)

  if (
    options.body &&
    !(options.body instanceof FormData) &&
    !headers.has('Content-Type')
  ) {
    headers.set('Content-Type', 'application/json')
  }

  if (token) {
    headers.set('Authorization', 'Bearer ' + token)
  }

  const response = await fetch(API_URL + endpoint, {
    ...options,
    headers,
  })

  if (response.status === 401) {
    logout()
    window.location.href = '/login'
  }

  return response
}

export default API_URL
