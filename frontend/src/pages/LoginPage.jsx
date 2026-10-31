import { useEffect, useRef, useState } from 'react'
import { ArrowRight, Eye, EyeOff, Info, Loader2, Lock, Mail, ShieldCheck, Users, Zap } from 'lucide-react'
import { api, session } from '../api'
import Logo from '../components/Logo'

/* Maillage facial décoratif (points + lignes dans un ovale), généré une fois. */
const MESH = (() => {
  const pts = []
  for (let r = 0; r < 11; r++) {
    const y = -1 + (2 * r) / 10
    const half = Math.sqrt(Math.max(0, 1 - y * y)) * (r > 7 ? 0.8 : 1)
    const n = Math.max(2, Math.round(half * 9))
    for (let c = 0; c < n; c++) {
      const x = n === 1 ? 0 : -half + (2 * half * c) / (n - 1)
      pts.push([150 + x * 92 + (r % 2 ? 3 : -3), 170 + y * 128])
    }
  }
  const lines = []
  pts.forEach((p, i) => {
    pts.map((q, j) => [j, Math.hypot(p[0] - q[0], p[1] - q[1])])
      .filter(([j, d]) => j > i && d < 34)
      .forEach(([j]) => lines.push([p, pts[j]]))
  })
  return { pts, lines }
})()

function FaceScan() {
  return (
    <svg className="facescan" viewBox="0 0 300 340" aria-hidden="true">
      <g className="mesh-lines">{MESH.lines.map(([a, b], i) => <line key={i} x1={a[0]} y1={a[1]} x2={b[0]} y2={b[1]} />)}</g>
      <g className="mesh-dots">{MESH.pts.map(([x, y], i) => <circle key={i} cx={x} cy={y} r="2.2" />)}</g>
      <g className="scan-corners">
        <path d="M20 60 V20 H60" /><path d="M240 20 H280 V60" />
        <path d="M20 280 V320 H60" /><path d="M240 320 H280 V280" />
      </g>
      <rect className="scan-line" x="24" y="30" width="252" height="3" rx="1.5" />
    </svg>
  )
}

const FEATURES = [
  [ShieldCheck, 'Sécurisé', 'Protection des données'],
  [Zap, 'Rapide', 'Résultats en temps réel'],
  [Users, 'Fiable', "Haute précision d'IA"],
]

export default function LoginPage({ onLogin }) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [show, setShow] = useState(false)
  const [remember, setRemember] = useState(true)
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState('')
  const [info, setInfo] = useState('')
  const [bgOk, setBgOk] = useState(true)
  const [googleId, setGoogleId] = useState(null)
  const googleBtn = useRef(null)

  const finish = (data) => {
    session.save(data, remember)
    onLogin(data.user)
  }

  const submit = async (e) => {
    e.preventDefault()
    setBusy(true); setErr(''); setInfo('')
    try { finish(await api.login(email.trim(), password, remember)) }
    catch (e2) { setErr(e2.message === 'Failed to fetch' ? 'Serveur injoignable. Lancez le backend (uvicorn).' : e2.message) }
    finally { setBusy(false) }
  }

  // Connexion Google : activée seulement si le serveur fournit un client_id
  useEffect(() => { api.authConfig().then((c) => setGoogleId(c.google_client_id)).catch(() => {}) }, [])
  useEffect(() => {
    if (!googleId) return
    const init = () => {
      window.google.accounts.id.initialize({
        client_id: googleId,
        callback: async ({ credential }) => {
          setBusy(true); setErr('')
          try { finish(await api.loginGoogle(credential, remember)) } catch (e) { setErr(e.message) } finally { setBusy(false) }
        },
      })
      if (googleBtn.current) {
        window.google.accounts.id.renderButton(googleBtn.current, { theme: 'outline', size: 'large', width: 380, text: 'signin_with', locale: 'fr' })
      }
    }
    if (window.google?.accounts) { init(); return }
    const s = document.createElement('script')
    s.src = 'https://accounts.google.com/gsi/client'
    s.async = true
    s.onload = init
    document.head.appendChild(s)
  }, [googleId]) // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className="login">
      {/* ===== Panneau gauche ===== */}
      <aside className={`login-hero ${bgOk ? 'with-photo' : ''}`}>
        {bgOk && <img className="hero-bg" src="/login-bg.jpg" alt="" onError={() => setBgOk(false)} />}
        <div className="hero-overlay" />
        {!bgOk && <FaceScan />}
        <div className="hero-edge" aria-hidden="true" />
        <div className="hero-logo"><Logo size="lg" /></div>
        <div className="hero-content">
          <h1>Système de<br /><span>reconnaissance faciale</span></h1>
          <span className="hero-bar" />
          <p>Une solution simple et sécurisée pour la vérification et l'identification des personnes avec Cires Technologies.</p>
          <div className="hero-features">
            {FEATURES.map(([Icon, title, text]) => (
              <div key={title} className="feature">
                <span className="feature-icon"><Icon size={26} fill="#f7a823" color="#0d1528" strokeWidth={1.5} /></span>
                <strong>{title}</strong>
                <small>{text}</small>
              </div>
            ))}
          </div>
        </div>
        <div className="hero-curve" />
      </aside>

      {/* ===== Panneau droit ===== */}
      <section className="login-side">
        <div className="side-curves" aria-hidden="true" />
        <form className="login-card" onSubmit={submit}>
          <div className="lc-logo"><Logo size="lg" /></div>
          <h2>Connexion à votre compte</h2>
          <p className="lc-sub">Accédez à la plateforme de reconnaissance faciale</p>

          <label className="lf">Adresse e-mail
            <div className="lf-input">
              <span className="lf-icon"><Mail size={18} /></span>
              <input type="email" autoComplete="username" placeholder="nom@entreprise.ma" value={email}
                onChange={(e) => setEmail(e.target.value)} required autoFocus />
            </div>
          </label>

          <label className="lf">Mot de passe
            <div className="lf-input">
              <span className="lf-icon"><Lock size={18} /></span>
              <input type={show ? 'text' : 'password'} autoComplete="current-password" placeholder="••••••••" value={password}
                onChange={(e) => setPassword(e.target.value)} required />
              <button type="button" className="lf-eye" onClick={() => setShow(!show)} aria-label={show ? 'Masquer le mot de passe' : 'Afficher le mot de passe'}>
                {show ? <Eye size={19} /> : <EyeOff size={19} />}
              </button>
            </div>
          </label>

          <div className="lf-row">
            <label className="check">
              <input type="checkbox" checked={remember} onChange={(e) => setRemember(e.target.checked)} />
              <span className="box" /> Se souvenir de moi
            </label>
            <button type="button" className="link" onClick={() => { setErr(''); setInfo("Contactez l'administrateur de la plateforme pour réinitialiser votre mot de passe.") }}>
              Mot de passe oublié ?
            </button>
          </div>

          {err && <p className="lf-error">{err}</p>}
          {info && <p className="lf-info"><Info size={16} /> {info}</p>}

          <button className="btn-login" disabled={busy}>
            {busy ? <Loader2 size={20} className="spin" /> : <>Se connecter <ArrowRight size={20} /></>}
          </button>

          <div className="divider"><span>ou</span></div>

          {googleId ? (
            <div className="google-official" ref={googleBtn} />
          ) : (
            <button type="button" className="btn-google"
              onClick={() => { setErr(''); setInfo('La connexion Google n\'est pas encore configurée (voir README : FV_GOOGLE_CLIENT_ID).') }}>
              <svg width="20" height="20" viewBox="0 0 48 48" aria-hidden="true">
                <path fill="#FFC107" d="M43.6 20.5H42V20H24v8h11.3C33.7 32.7 29.2 36 24 36c-6.6 0-12-5.4-12-12s5.4-12 12-12c3.1 0 5.8 1.2 7.9 3.1l5.7-5.7C34 6.1 29.3 4 24 4 12.9 4 4 12.9 4 24s8.9 20 20 20 20-8.9 20-20c0-1.3-.1-2.4-.4-3.5z" />
                <path fill="#FF3D00" d="M6.3 14.7l6.6 4.8C14.7 15.1 19 12 24 12c3.1 0 5.8 1.2 7.9 3.1l5.7-5.7C34 6.1 29.3 4 24 4 16.3 4 9.7 8.3 6.3 14.7z" />
                <path fill="#4CAF50" d="M24 44c5.2 0 9.9-2 13.4-5.2l-6.2-5.2C29.2 35.1 26.7 36 24 36c-5.2 0-9.6-3.3-11.3-8l-6.5 5C9.5 39.6 16.2 44 24 44z" />
                <path fill="#1976D2" d="M43.6 20.5H42V20H24v8h11.3c-.8 2.2-2.2 4.2-4.1 5.6l6.2 5.2C37 39.2 44 34 44 24c0-1.3-.1-2.4-.4-3.5z" />
              </svg>
              Se connecter avec Google
            </button>
          )}
        </form>
      </section>
    </div>
  )
}
