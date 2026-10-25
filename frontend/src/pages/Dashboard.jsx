function Dashboard() {
  return (
    <div className="app">
      <header className="app-header">
        <div className="app-header-inner">
          <h1>WindSight</h1>
          <p>UK Wind Forecast Intelligence</p>
        </div>
      </header>

      <main className="app-main">
        <section className="card">
          <h2>Frontend is running</h2>
          <p>
            This page compares Elexon wind generation forecasts with actual wind generation
            for January 2026.
          </p>
          <p className="muted">
            The real dashboard (metrics, chart and data table) is added in the next steps.
          </p>
        </section>
      </main>
    </div>
  )
}

export default Dashboard