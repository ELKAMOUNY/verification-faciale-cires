import { useState } from 'react'
import { Check, CheckCircle2, Image as ImageIcon, Loader2, User, Users, XCircle } from 'lucide-react'
import { api } from '../api'
import CardHeader from '../components/CardHeader'
import FaceBoxes from '../components/FaceBoxes'
import ImageInput from '../components/ImageInput'
import PageHeader from '../components/PageHeader'
import ScoreBar from '../components/ScoreBar'

/** Vérification 1:1 — contre une personne de la galerie, ou entre deux photos. */
export default function VerifyPage({ persons }) {
  const [mode, setMode] = useState('gallery')
  const [personId, setPersonId] = useState('')
  const [file, setFile] = useState(null)
  const [file2, setFile2] = useState(null)
  const [res, setRes] = useState(null)
  const [err, setErr] = useState('')
  const [busy, setBusy] = useState(false)

  const person = persons.find((p) => p.id === personId)
  const ready = mode === 'gallery' ? file && personId : file && file2

  const run = async () => {
    setBusy(true); setErr(''); setRes(null)
    try {
      setRes(mode === 'gallery' ? await api.verify(personId, file) : await api.compare(file, file2))
    } catch (e) { setErr(e.message) } finally { setBusy(false) }
  }
  const reset = (fn) => (v) => { fn(v); setRes(null) }

  return (
    <section>
      <PageHeader title="Vérification faciale">
        La vérification répond à la question : <em>« Cette photo est-elle bien la personne déclarée ? »</em>
      </PageHeader>

      <div className="mode-switch">
        <button className={mode === 'gallery' ? 'on' : ''} onClick={() => { setMode('gallery'); setRes(null) }}>
          <ImageIcon size={18} /> Photo ↔ personne de la galerie
        </button>
        <button className={mode === 'pair' ? 'on' : ''} onClick={() => { setMode('pair'); setRes(null) }}>
          <Users size={18} /> Photo ↔ photo
        </button>
      </div>

      <div className="grid2">
        <ImageInput
          label="Photo à vérifier"
          onChange={reset(setFile)}
          overlay={res?.box && <FaceBoxes width={res.width} height={res.height} faces={[{ box: res.box, ok: res.match }]} />}
        />
        {mode === 'gallery' ? (
          <div className="card">
            <CardHeader icon={User} title="Identité déclarée" subtitle="Sélectionnez la personne à vérifier" />
            <div className="select-wrap">
              <select value={personId} onChange={(e) => reset(setPersonId)(e.target.value)}>
                <option value="">— choisir —</option>
                {persons.map((p) => <option key={p.id} value={p.id}>{p.id} · {p.name}</option>)}
              </select>
            </div>
            {person && (
              <>
                <div className="thumbs">
                  {person.images.map((im) => <img key={im} src={api.imageUrl(person.id, im)} alt="" />)}
                </div>
                <p className="hint">{person.n_faces} image(s) de référence</p>
              </>
            )}
          </div>
        ) : (
          <ImageInput label="Deuxième photo" subtitle="Photo à comparer avec la première" onChange={reset(setFile2)} />
        )}
      </div>

      <button className="btn-cta" disabled={!ready || busy} onClick={run}>
        {busy ? <Loader2 size={20} className="spin" /> : <Check size={20} strokeWidth={3} />}
        {busy ? 'Analyse…' : 'Vérifier'}
      </button>
      {err && <p className="error">{err}</p>}

      {res && (
        <div className={`verdict ${res.match ? 'ok' : 'ko'}`}>
          <div className="verdict-head">
            {res.match ? <CheckCircle2 size={28} /> : <XCircle size={28} />}
            <div>
              <h2>{res.match ? 'Même personne' : 'Personne différente'}</h2>
              <p>
                Similarité : <strong>{res.score}</strong>
                {res.mean != null && <span className="muted"> · moyenne sur les références : {res.mean}</span>}
              </p>
            </div>
          </div>
          <ScoreBar score={res.score} threshold={res.threshold} />
        </div>
      )}
    </section>
  )
}
