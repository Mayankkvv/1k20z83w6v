function MetricCard({ label, value, description, detail }) {
  return (
    <article className="card metric-card">
      <h3 className="metric-label">{label}</h3>
      <p className="metric-value">{value}</p>
      {detail && <p className="metric-detail">{detail}</p>}
      <p className="metric-description muted">{description}</p>
    </article>
  )
}

export default MetricCard