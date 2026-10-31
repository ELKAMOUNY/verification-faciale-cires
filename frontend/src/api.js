export const BASE = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api'

/* ---------- Session (jeton) ---------- */
const KEY = 'fv_session'

export const session = {
  get() {
    try {
      const raw = localStorage.getItem(KEY) || sessionStorage.getItem(KEY)
      const s = raw ? JSON.parse(raw) : null
      if (s && s.expires * 1000 < Date.now()) { session.clear(); return null }
      return s
    } catch { return null }
  },
  save(data, remember) {
    session.clear()
    try { (remember ? localStorage : sessionStorage).setItem(KEY, JSON.stringify(data)) } catch { /* stockage indisponible */ }
  },
  clear() {
    try { localStorage.removeItem(KEY); sessionStorage.removeItem(KEY) } catch { /* rien */ }
  },
  token() { return session.get()?.token || '' },
}

let onUnauthorized = () => {}
export const setUnauthorizedHandler = (fn) => { onUnauthorized = fn }

async function call(path, options = {}) {
  const headers = { ...(options.headers || {}) }
  const t = session.token()
  if (t) headers.Authorization = `Bearer ${t}`
  const res = await fetch(BASE + path, { ...options, headers })
  const data = await res.json().catch(() => ({}))
  if (res.status === 401 && !path.startsWith('/auth/login')) {
    session.clear()
    onUnauthorized()
  }
  if (!res.ok) throw new Error(data.detail || `Erreur ${res.status}`)
  return data
}

const json = (body) => ({ method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })

function form(fields) {
  const fd = new FormData()
  Object.entries(fields).forEach(([k, v]) => {
    if (Array.isArray(v)) v.forEach((x) => fd.append(k, x))
    else fd.append(k, v)
  })
  return { method: 'POST', body: fd }
}

export const api = {
  // Authentification
  login: (email, password, remember) => call('/auth/login', json({ email, password, remember })),
  loginGoogle: (credential, remember) => call('/auth/google', json({ credential, remember })),
  authConfig: () => call('/auth/config'),
  me: () => call('/auth/me'),
  // Application
  health: () => call('/health'),
  persons: () => call('/persons'),
  imageUrl: (pid, name) => `${BASE}/persons/${pid}/images/${name}?token=${encodeURIComponent(session.token())}`,
  addPerson: (name, files) => call('/persons', form({ name, files })),
  reload: () => call('/reload', { method: 'POST' }),
  verify: (person_id, file) => call('/verify', form({ person_id, file })),
  compare: (file1, file2) => call('/compare', form({ file1, file2 })),
  identify: (file) => call('/identify', form({ file })),
  evaluate: (threshold) => call(`/evaluate${threshold != null ? `?threshold=${threshold}` : ''}`),
}
