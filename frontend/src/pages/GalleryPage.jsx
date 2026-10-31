import { useState } from 'react'
import { Loader2, RefreshCw, UserPlus } from 'lucide-react'
import { api } from '../api'
import CardHeader from '../components/CardHeader'
import PageHeader from '../components/PageHeader'

/** Galerie : data/reference/person_xxx + ajout d'une nouvelle personne. */
export default function GalleryPage({ persons, onChange }) {
  const [name, setName] = useState('')
  const [files, setFiles] = useState([])
  const [msg, setMsg] = useState('')
  const [busy, setBusy] = useState(false)
  const [q, setQ] = useState('')

  const add = async (e) => {
    e.preventDefault()
    setBusy(true); setMsg('')
    try {
      const r = await api.addPerson(name.trim(), [...files])
      setMsg(`${r.name} ajouté(e) : ${r.id} (${r.saved} image(s), ${r.rejected} rejetée(s))`)
      setName(''); setFiles([]); e.target.reset()
      onChange()
    } catch (err) { setMsg('Erreur : ' + err.message) } finally { setBusy(false) }
  }

  const shown = persons.filter((p) => `${p.id} ${p.name}`.toLowerCase().includes(q.toLowerCase()))

  return (
    <section>
      <PageHeader title="Galerie des identités">
        Personnes enregistrées dans <code>data/reference</code>, utilisées comme références pour la vérification.
      </PageHeader>

      <form className="card add" onSubmit={add}>
        <CardHeader icon={UserPlus} title="Ajouter une personne" subtitle="3 photos de face conseillées, bien éclairées" />
        <div className="row-form">
          <label className="field">Nom complet<input value={name} onChange={(e) => setName(e.target.value)} required /></label>
          <label className="field">Photos<input type="file" accept="image/*" multiple required onChange={(e) => setFiles(e.target.files)} /></label>
          <button className="btn-primary" disabled={busy}>
            {busy ? <Loader2 size={18} className="spin" /> : <UserPlus size={18} />} Ajouter
          </button>
        </div>
        {msg && <p className="msg">{msg}</p>}
      </form>

      <div className="toolbar">
        <input className="search" placeholder="Rechercher un nom…" value={q} onChange={(e) => setQ(e.target.value)} />
        <span className="muted">{shown.length} / {persons.length} personne(s)</span>
        <button className="btn-ghost" onClick={() => api.reload().then(onChange)}><RefreshCw size={16} /> Recharger le dossier</button>
      </div>

      {persons.length === 0 && (
        <p className="alert">Galerie vide. Lancez <code>python data/download_dataset.py</code> pour télécharger les données en ligne.</p>
      )}
      <div className="gallery">
        {shown.map((p) => (
          <div key={p.id} className="person">
            <div className="person-thumbs">
              {p.images.slice(0, 3).map((im) => <img key={im} src={api.imageUrl(p.id, im)} alt="" loading="lazy" />)}
            </div>
            <div className="person-info">
              <strong>{p.name}</strong>
              <span className="muted">{p.id}</span>
            </div>
            <span className="badge">{p.n_faces}/{p.n_images} visages</span>
          </div>
        ))}
      </div>
    </section>
  )
}
