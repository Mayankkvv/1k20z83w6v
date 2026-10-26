import { useEffect, useState } from 'react'
import AccuracySection from '../components/AccuracySection.jsx'
import ExplorerSection from '../components/ExplorerSection.jsx'
import OverviewSection from '../components/OverviewSection.jsx'
import StatusMessage from '../components/StatusMessage.jsx'
import { getOverview } from '../services/api.js'

function Dashboard() {
  const [overview, setOverview] = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(true)
  const [reloadKey, setReloadKey] = useState(0)
  // The delivery date shown in the explorer. The daily accuracy chart can change it too.
  const [selectedDate, setSelectedDate] = useState(null)

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

  // Called when a day is clicked in the accuracy chart: select it and scroll to the explorer.
  function handleSelectFromChart(date) {
    setSelectedDate(date)
    document.getElementById('explorer')?.scrollIntoView({ block: 'start' })
  }

  const ready = overview && !loading && !error
  // Until the user picks a date, show the first day of the period.
  const activeDate = selectedDate || (overview ? overview.period.start : null)

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

        {ready && (
          <>
            <OverviewSection overview={overview} />
            <AccuracySection
              selectedDate={activeDate}
              onSelectDate={handleSelectFromChart}
              monthMae={overview.metrics.mae_mw}
            />
            <ExplorerSection
              selectedDate={activeDate}
              onDateChange={setSelectedDate}
              minDate={overview.period.start}
              maxDate={overview.period.end}
              monthMetrics={overview.metrics}
            />
          </>
        )}
      </main>
    </div>
  )
}

export default Dashboard