/** Titre de page avec trait orange, comme sur la maquette. */
export default function PageHeader({ title, children }) {
  return (
    <div className="page-header">
      <span className="accent" />
      <h1>{title}</h1>
      {children && <p>{children}</p>}
    </div>
  )
}
