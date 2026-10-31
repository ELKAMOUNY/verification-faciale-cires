/** Rectangles des visages dessinés par-dessus une image (coordonnées de l'API). */
export default function FaceBoxes({ width, height, faces }) {
  if (!width || !faces?.length) return null
  return (
    <svg className="boxes" viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="none">
      {faces.map((f, i) => {
        const [x, y, w, h] = f.box
        const fs = Math.max(14, width / 35)
        return (
          <g key={i} className={f.ok ? 'ok' : 'ko'}>
            <rect x={x} y={y} width={w} height={h} strokeWidth={Math.max(2, width / 250)} />
            {f.label && <text x={x} y={Math.max(fs, y - 6)} fontSize={fs}>{f.label}</text>}
          </g>
        )
      })}
    </svg>
  )
}
