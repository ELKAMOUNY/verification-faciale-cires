/** En-tête de carte : pastille icône + titre + sous-titre (+ actions à droite). */
export default function CardHeader({ icon: Icon, title, subtitle, children }) {
  return (
    <div className="card-header">
      <span className="pastille"><Icon size={22} /></span>
      <div className="ch-text">
        <h3>{title}</h3>
        {subtitle && <p>{subtitle}</p>}
      </div>
      {children && <div className="ch-actions">{children}</div>}
    </div>
  )
}
