import { useState } from 'react'
import { BarChart3, Loader2, Play, SlidersHorizontal } from 'lucide-react'
import { api } from '../api'
import CardHeader from '../components/CardHeader'
import Histogram from '../components/Histogram'
import PageHeader from '../components/PageHeader'

const pct = (v) => `${(v * 100).toFixed(1)} %`

/** Évaluation sur data/test : FAR, FRR, EER, précision. */
export default function EvaluationPage() {
  const [threshold, setThreshold] = useState(0.363)
  const [res, setRes] = useState(null)
  const [err, setErr] = useState('')
  const [busy, setBusy] = useState(false)

  const run = async (t = threshold) => {
    setBusy(true); setErr('')
    try { setRes(await api.evaluate(t)) } catch (e) { setErr(e.message) } finally { setBusy(false) }
  }

  return (
    <section>
      <PageHeader title="Évaluation du modèle">
        Chaque image de <code>data/test</code> est comparée à sa vraie identité (paires « genuine ») et à toutes les autres (paires « imposteur »).
      </PageHeader>

      <div className="card controls">
        <CardHeader icon={SlidersHorizontal} title="Seuil de décision" subtitle="Plus haut = plus sûr (FAR ↓), plus bas = plus tolérant (FRR ↓)" />
        <div className="controls-row">
          <input type="range" min="0" max="1" step="0.005" value={threshold}
            onChange={(e) => setThreshold(+e.target.value)} onMouseUp={() => res && run()} onTouchEnd={() => res && run()} />
          <span className="thr-value">{threshold.toFixed(3)}</span>
          <button className="btn-cta small" onClick={() => run()} disabled={busy}>
            {busy ? <Loader2 size={20} className="spin" /> : <Play size={20} />} Lancer l'évaluation
          </button>
        </div>
      </div>

      {err && <p className="error">{err}</p>}
      {res && (
        <>
          <div className="metrics">
            <Metric label="Précision vérification" value={pct(res.verification_accuracy)} />
            <Metric label="Identification rang 1" value={pct(res.identification_rank1)} />
            <Metric label="FAR · imposteurs acceptés" value={pct(res.FAR)} />
            <Metric label="FRR · vrais refusés" value={pct(res.FRR)} />
            <Metric label="EER" value={pct(res.EER)} hint={`au seuil ${res.EER_threshold}`} />
            <Metric label="Paires testées" value={res.n_genuine + res.n_impostor} hint={`${res.n_test_images} images`} />
          </div>
          <div className="card">
            <CardHeader icon={BarChart3} title="Distribution des scores" subtitle="Les deux groupes doivent être séparés par le seuil" />
            <Histogram data={res.histogram} threshold={res.threshold} />
          </div>
        </>
      )}
    </section>
  )
}

function Metric({ label, value, hint }) {
  return (
    <div className="metric">
      <span className="m-label">{label}</span>
      <strong>{value}</strong>
      {hint && <span className="m-hint">{hint}</span>}
    </div>
  )
}
