import { useCallback, useEffect, useRef, useState } from 'react'
import { BarChart3, ChevronDown, Globe, Image as ImageIcon, LogOut, ShieldCheck, User, Users } from 'lucide-react'
import { api, session, setUnauthorizedHandler } from './api'
import Logo from './components/Logo'
import EvaluationPage from './pages/EvaluationPage'
import GalleryPage from './pages/GalleryPage'
import IdentifyPage from './pages/IdentifyPage'
import LoginPage from './pages/LoginPage'
import VerifyPage from './pages/VerifyPage'

const PAGES = [
  ['verify', 'Vérification 1:1', ShieldCheck],
  ['identify', 'Identification 1:N', Users],
  ['gallery', 'Galerie', ImageIcon],
  ['evaluation', 'Évaluation', BarChart3],
]

/** Porte d'entrée : page de connexion tant qu'il n'y a pas de session valide. */
export default function App() {
  const [user, setUser] = useState(() => session.get()?.user || null)

  const logout = useCallback(() => { session.clear(); setUser(null) }, [])
  useEffect(() => { setUnauthorizedHandler(() => setUser(null)) }, [])

  // Vérifie que la session sauvegardée est toujours valide côté serveur
  useEffect(() => { if (user) api.me().catch(() => {}) }, []) // eslint-disable-line react-hooks/exhaustive-deps

  if (!user) return <LoginPage onLogin={setUser} />
  return <MainApp user={user} onLogout={logout} />
}

function UserMenu({ user, onLogout }) {
  const [open, setOpen] = useState(false)
  const ref = useRef(null)
  useEffect(() => {
    const close = (e) => { if (ref.current && !ref.current.contains(e.target)) setOpen(false) }
    document.addEventListener('mousedown', close)
    return () => document.removeEventListener('mousedown', close)
  }, [])
  return (
    <div className="usermenu" ref={ref}>
      <button className="um-trigger" onClick={() => setOpen(!open)} aria-label="Menu utilisateur">
        <span className="avatar"><User size={16} /></span>
        <ChevronDown size={16} />
      </button>
      {open && (
        <div className="um-panel">
          <strong>{user.name}</strong>
          <span>{user.email}</span>
          <span className="badge">{user.role === 'admin' ? 'Administrateur' : 'Utilisateur'}</span>
          <button onClick={onLogout}><LogOut size={16} /> Se déconnecter</button>
        </div>
      )}
    </div>
  )
}

function MainApp({ user, onLogout }) {
  const [page, setPage] = useState('verify')
  const [persons, setPersons] = useState([])
  const [health, setHealth] = useState(null)
  const [down, setDown] = useState(false)

  const refresh = useCallback(() => {
    Promise.all([api.health(), api.persons()])
      .then(([h, p]) => { setHealth(h); setPersons(p); setDown(false) })
      .catch(() => setDown(true))
  }, [])
  useEffect(refresh, [refresh])

  return (
    <div className="shell">
      <div className="topbar">
        <div className="topbar-inner">
          <div className="tb-left">
            <span className="tb-org">TANGER MED</span>
            <span className="tb-sep" />
            <Globe size={18} />
            <span className="tb-platform">Plateforme CIRES Technologies</span>
          </div>
          <div className="tb-right">
            <Users size={18} />
            <span>{health ? `${health.persons} personne(s) · seuil ${health.threshold}` : 'Connexion…'}</span>
            <span className="tb-sep" />
            <UserMenu user={user} onLogout={onLogout} />
          </div>
        </div>
      </div>

      <header className="navbar">
        <div className="navbar-inner">
          <Logo />
          <nav>
            {PAGES.map(([k, label, Icon]) => (
              <button key={k} className={page === k ? 'active' : ''} onClick={() => setPage(k)}>
                <Icon size={18} />
                <span>{label}</span>
              </button>
            ))}
          </nav>
        </div>
      </header>

      <div className="bg-arcs" aria-hidden="true" />

      <main className="content">
        {down && (
          <p className="alert">Backend injoignable. Dans <code>backend/</code> : <code>uvicorn main:app --reload</code></p>
        )}
        {page === 'verify' && <VerifyPage persons={persons} />}
        {page === 'identify' && <IdentifyPage />}
        {page === 'gallery' && <GalleryPage persons={persons} onChange={refresh} />}
        {page === 'evaluation' && <EvaluationPage />}
      </main>
    </div>
  )
}
