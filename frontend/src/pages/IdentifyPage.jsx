import { useState } from 'react'
import { ListOrdered, Loader2, ScanSearch } from 'lucide-react'
import { api } from '../api'
import CardHeader from '../components/CardHeader'
import FaceBoxes from '../components/FaceBoxes'
import ImageInput from '../components/ImageInput'
import PageHeader from '../components/PageHeader'

/** Identification 1:N — « Qui est sur cette photo ? » (plusieurs visages possibles) */
export default function IdentifyPage() {
  const [file, setFile] = useState(null)
  const [res, setRes] = useState(null)
  const [err, setErr] = useState('')
  const [busy, setBusy] = useState(false)

  const run = async () => {
    setBusy(true); setErr(''); setRes(null)
    try { setRes(await api.identify(file)) } catch (e) { setErr(e.message) } finally { setBusy(false) }
  }

  const faces = res?.faces.map((f, i) => ({
    box: f.box, ok: !!f.best, label: `${i + 1}. ${f.best ? f.best.name : 'Inconnu'}`,
  }))

  return (
    <section>
      <PageHeader title="Identification faciale">
        L'identification répond à la question : <em>« Qui est sur cette photo ? »</em> Chaque visage est comparé à toute la galerie.
      </PageHeader>

      <div className="grid2">
        <ImageInput label="Photo à analyser" onChange={(f) => { setFile(f); setRes(null) }}
          overlay={res && <FaceBoxes width={res.width} height={res.height} faces={faces} />} />

        <div className="card">
          <CardHeader icon={ListOrdered} title="Résultats" subtitle="Les 5 identités les plus proches par visage" />
          {!res && !err && <p className="empty">Choisissez une photo puis lancez l'identification.</p>}
          {err && <p className="error">{err}</p>}
          {res?.faces.map((f, i) => (
            <div key={i} className="face-result">
              <div className="fr-head">
                <span className="badge">Visage {i + 1}</span>
                <strong className={f.best ? 'ok' : 'ko'}>{f.best ? f.best.name : 'Inconnu'}</strong>
              </div>
              {f.ranking.length === 0 && (
                <p className="error">Aucun visage de référence chargé : ouvrez la Galerie (chaque personne doit avoir au moins 1 visage) puis « Recharger le dossier ».</p>
              )}
              {f.ranking.map((r) => (
                <div key={r.person_id} className="rank-row">
                  <span className="rank-name">{r.name}</span>
                  <div className="rank-bar"><div style={{ width: `${Math.max(0, r.score) * 100}%` }} className={r.score >= res.threshold ? 'ok' : ''} /></div>
                  <span className="rank-score">{r.score.toFixed(3)}</span>
                </div>
              ))}
            </div>
          ))}
        </div>
      </div>

      <button className="btn-cta" disabled={!file || busy} onClick={run}>
        {busy ? <Loader2 size={20} className="spin" /> : <ScanSearch size={20} />}
        {busy ? 'Analyse…' : 'Identifier'}
      </button>
    </section>
  )
}
