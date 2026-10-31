import { useEffect, useRef, useState } from 'react'
import { Camera, FileText, Image as ImageIcon, UploadCloud, Video } from 'lucide-react'
import CardHeader from './CardHeader'

/** Carte de saisie d'image : glisser-déposer / fichier / webcam. Renvoie un File via onChange. */
export default function ImageInput({ label, subtitle = 'Téléchargez une photo ou utilisez votre webcam', onChange, overlay }) {
  const [mode, setMode] = useState('file')
  const [preview, setPreview] = useState(null)
  const [drag, setDrag] = useState(false)
  const [camError, setCamError] = useState('')
  const videoRef = useRef(null)
  const inputRef = useRef(null)

  useEffect(() => {
    if (mode !== 'cam') return
    let stream
    setCamError('')
    navigator.mediaDevices
      ?.getUserMedia({ video: { width: 640, height: 480 } })
      .then((s) => { stream = s; if (videoRef.current) videoRef.current.srcObject = s })
      .catch(() => setCamError("Caméra inaccessible. Autorisez l'accès dans le navigateur."))
    return () => stream?.getTracks().forEach((t) => t.stop())
  }, [mode])

  const pick = (file) => {
    if (!file || !file.type.startsWith('image/')) return
    setPreview((old) => { if (old) URL.revokeObjectURL(old); return URL.createObjectURL(file) })
    onChange(file)
  }

  const capture = () => {
    const v = videoRef.current
    if (!v?.videoWidth) return
    const c = document.createElement('canvas')
    c.width = v.videoWidth
    c.height = v.videoHeight
    c.getContext('2d').drawImage(v, 0, 0)
    c.toBlob((b) => { pick(new File([b], 'webcam.jpg', { type: 'image/jpeg' })); setMode('file') }, 'image/jpeg', 0.9)
  }

  return (
    <div className="card">
      <CardHeader icon={ImageIcon} title={label} subtitle={subtitle}>
        <div className="toggle">
          <button type="button" className={mode === 'file' ? 'on' : ''} onClick={() => setMode('file')}>
            <FileText size={16} /> Fichier
          </button>
          <button type="button" className={mode === 'cam' ? 'on' : ''} onClick={() => setMode('cam')}>
            <Video size={16} /> Webcam
          </button>
        </div>
      </CardHeader>

      {mode === 'cam' ? (
        <div className="dropzone cam">
          {camError ? <p className="muted">{camError}</p> : <video ref={videoRef} autoPlay playsInline muted />}
          {!camError && (
            <button type="button" className="btn-primary capture" onClick={capture}>
              <Camera size={18} /> Capturer
            </button>
          )}
        </div>
      ) : (
        <div
          className={`dropzone ${drag ? 'drag' : ''} ${preview ? 'has-img' : ''}`}
          onClick={() => inputRef.current?.click()}
          onDragOver={(e) => { e.preventDefault(); setDrag(true) }}
          onDragLeave={() => setDrag(false)}
          onDrop={(e) => { e.preventDefault(); setDrag(false); pick(e.dataTransfer.files[0]) }}
        >
          {preview ? (
            <div className="preview">
              <img src={preview} alt="" />
              {overlay}
            </div>
          ) : (
            <div className="dz-empty">
              <UploadCloud size={48} strokeWidth={1.3} />
              <strong>Glissez-déposez une photo ici</strong>
              <span>ou cliquez pour choisir un fichier</span>
              <small>JPG, PNG, WEBP · Max 10 Mo</small>
            </div>
          )}
          <input ref={inputRef} type="file" accept="image/*" hidden onChange={(e) => pick(e.target.files[0])} />
        </div>
      )}
      {preview && mode === 'file' && <p className="hint">Cliquez sur l'image ou déposez-en une autre pour la remplacer.</p>}
    </div>
  )
}
