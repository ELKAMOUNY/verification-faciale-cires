/** Distribution des scores : vraies paires (genuine) vs imposteurs. */
export default function Histogram({ data, threshold }) {
  const { bins, genuine, impostor } = data
  const W = 640, H = 220, P = 30
  const step = bins[1] - bins[0]
  const xmin = bins[0], xmax = bins[bins.length - 1] + step
  const norm = (arr) => { const s = arr.reduce((a, b) => a + b, 0) || 1; return arr.map((v) => v / s) }
  const g = norm(genuine), im = norm(impostor)
  const ymax = Math.max(...g, ...im) || 1
  const X = (v) => P + ((v - xmin) / (xmax - xmin)) * (W - 2 * P)
  const TOP = 48 // espace réservé à la légende
  const Y = (v) => H - P - (v / ymax) * (H - P - TOP)
  const bw = X(xmin + step) - X(xmin)
  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="hist">
      <line x1={P} y1={H - P} x2={W - P} y2={H - P} className="axis" />
      {bins.map((b, i) => (
        <g key={i}>
          <rect x={X(b) + 1} y={Y(im[i])} width={bw - 2} height={H - P - Y(im[i])} className="imp" />
          <rect x={X(b) + 1} y={Y(g[i])} width={bw - 2} height={H - P - Y(g[i])} className="gen" />
        </g>
      ))}
      <line x1={X(threshold)} x2={X(threshold)} y1={TOP - 8} y2={H - P} className="thr" />
      <text x={X(threshold) + 4} y={TOP} className="lbl">seuil {threshold}</text>
      {[0, 0.25, 0.5, 0.75, 1].map((t) => (
        <text key={t} x={X(t)} y={H - 10} textAnchor="middle" className="lbl">{t}</text>
      ))}
      <g transform={`translate(${P + 4}, 6)`}>
        <rect width="12" height="12" className="gen" /><text x="18" y="10" className="lbl">même personne</text>
        <rect x="140" width="12" height="12" className="imp" /><text x="158" y="10" className="lbl">personnes différentes</text>
      </g>
    </svg>
  )
}
