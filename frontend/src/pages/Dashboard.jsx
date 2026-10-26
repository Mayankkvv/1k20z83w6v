import { useEffect, useState } from 'react'
import OverviewSection from '../components/OverviewSection.jsx'
import StatusMessage from '../components/StatusMessage.jsx'
import { getOverview } from '../services/api.js'

function Dashboard() {
  const [overview, setOverview] = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(true)
  const [reloadKey, setReloadKey] = useState(0)

  // Load the monthly overview when the page opens, and again after "Try again".
  useEffect(() => {
    let cancelled = false

    getOverview()
      .then((data) => {
        if (!cancelled) {
          setOverview(data)
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err.message)
        }
      })
      .finally(() => {
        if (!cancelled) {
          setLoading(false)
        }
      })

    return () => {
      cancelled = true
    }
  }, [reloadKey])

  function handleRetry() {
    setLoading(true)
    setError(null)
    setReloadKey((key) => key + 1)
  }

  return (
    <div className="app">
      <header className="app-header">
        <div className="app-header-inner">
          <h1>WindSight</h1>
          <p>UK Wind Forecast Intelligence</p>
        </div>
      </header>

      <main className="app-main">
        {loading && (
          <StatusMessage
            kind="loading"
            title="Loading January 2026 data"
            message="The first load fetches data from Elexon and can take up to a minute."
          />
        )}

        {error && (
          <StatusMessage
            kind="error"
            title="Could not load the data"
            message={error}
            actionLabel="Try again"
            onAction={handleRetry}
          />
        )}

        {overview && !loading && !error && <OverviewSection overview={overview} />}
      </main>
    </div>
  )
}

export default Dashboard