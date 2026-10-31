/** Similarité cosinus affichée sur 0..1 avec le seuil de décision. */
export default function ScoreBar({ score, threshold }) {
  const pct = (v) => `${Math.min(100, Math.max(0, v * 100))}%`
  return (
    <div className="scorebar">
      <div className="track">
        <div className={`fill ${score >= threshold ? 'ok' : 'ko'}`} style={{ width: pct(score) }} />
        <div className="mark" style={{ left: pct(threshold) }} />
      </div>
      <div className="scale"><span>0</span><span style={{ left: pct(threshold) }}>seuil {threshold}</span><span>1</span></div>
    </div>
  )
}
