import { useState } from 'react'
import { ScanFace } from 'lucide-react'

/** Logo : utilise /logo.png s'il existe (dossier public), sinon un logo texte. */
export default function Logo({ size = 'md' }) {
  const [hasImg, setHasImg] = useState(true)
  return (
    <div className={`brand brand-${size}`}>
      {hasImg ? (
        <img src="/logo.png" alt="CIRES Technologies" className="brand-img" onError={() => setHasImg(false)} />
      ) : (
        <>
          <div className="brand-text">
            <strong>CIRES</strong>
            <span>TECHNOLOGIES</span>
          </div>
          <div className="brand-mark"><ScanFace size={size === 'lg' ? 28 : 22} strokeWidth={2.2} /></div>
        </>
      )}
    </div>
  )
}
