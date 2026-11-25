// frontend/src/lib/api.ts
const BASE =
  (import.meta as any).env?.VITE_API_URL ||
  (typeof window !== 'undefined' && window.location.port === '5173'
    ? 'http://localhost:8000'
    : '')

const TOKEN_KEY = 'concursosai_token'

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY)
}
export function setToken(token: string) {
  localStorage.setItem(TOKEN_KEY, token)
}
export function clearToken() {
  localStorage.removeItem(TOKEN_KEY)
}

type Opcoes = { method?: string; body?: any; timeout?: number }

export async function api<T = any>(path: string, opcoes: Opcoes = {}): Promise<T> {
  const { method = 'GET', body, timeout = 45000 } = opcoes
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), timeout)
  try {
    const resp = await fetch(`${BASE}${path}`, {
      method,
      headers: {
        'Content-Type': 'application/json',
        ...(getToken() ? { Authorization: `Bearer ${getToken()}` } : {}),
      },
      body: body === undefined ? undefined : JSON.stringify(body),
      signal: controller.signal,
    })
    const texto = await resp.text()
    const dados = texto ? JSON.parse(texto) : null
    if (!resp.ok) {
      const detalhe = (dados && (dados.detail || dados.erro || dados.message)) || `HTTP ${resp.status}`
      const msg = typeof detalhe === 'string' ? detalhe : detalhe.erro || JSON.stringify(detalhe)
      throw new Error(msg)
    }
    return dados as T
  } finally {
    clearTimeout(timer)
  }
}

export const brl = (v?: number | null) =>
  v == null ? '—' : v.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })

export const dataBR = (iso?: string | null) => {
  if (!iso) return 'a definir'
  const [a, m, d] = iso.split('-')
  return d && m && a ? `${d}/${m}/${a}` : iso
}
