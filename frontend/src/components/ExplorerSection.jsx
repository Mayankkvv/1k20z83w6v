import { useEffect, useState } from 'react'
import DataTable from './DataTable.jsx'
import DateSelector from './DateSelector.jsx'
import DayMetrics from './DayMetrics.jsx'
import ForecastChart from './ForecastChart.jsx'
import StatusMessage from './StatusMessage.jsx'
import { getDay } from '../services/api.js'
import { formatTimestamp } from '../utils/format.js'

const FIRST_DATE = '2026-01-01'
const LAST_DATE = '2026-01-31'

function ExplorerSection() {
  const [selectedDate, setSelectedDate] = useState(FIRST_DATE)
  const [day, setDay] = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(true)
  const [reloadKey, setReloadKey] = useState(0)

  // Load the selected day whenever the date changes (or after "Try again").
  useEffect(() => {
    let cancelled = false

    getDay(selectedDate)
      .then((data) => {
        if (!cancelled) {
          setDay(data)
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
  }, [selectedDate, reloadKey])

  function handleDateChange(newDate) {
    setSelectedDate(newDate)
    setLoading(true)
    setError(null)
  }

  function handleRetry() {
    setLoading(true)
    setError(null)
    setReloadKey((key) => key + 1)
  }

  const hasAnyData = day ? day.rows.some((row) => row.forecast_mw !== null || row.actual_mw !== null) : false
  const showDay = day && !loading && !error

  return (
    <section>
      <div className="section-heading">
        <h2>Forecast explorer</h2>
        <p className="muted">
          Pick a delivery date to compare the forecast available at decision time with what
          wind farms actually generated. All times are UTC, which equals UK time in January.
        </p>
      </div>

      <div className="card explorer-controls">
        <DateSelector
          value={selectedDate}
          minDate={FIRST_DATE}
          maxDate={LAST_DATE}
          onChange={handleDateChange}
        />
      </div>

      {loading && (
        <StatusMessage
          kind="loading"
          title={`Loading ${selectedDate}`}
          message="Fetching the hourly forecast and actual generation."
        />
      )}

      {error && (
        <StatusMessage
          kind="error"
          title="Could not load this day"
          message={error}
          actionLabel="Try again"
          onAction={handleRetry}
        />
      )}

      {showDay && (
        <>
          <div className="card day-intro">
            <h3>Delivery date {day.date}</h3>
            <p>
              Each forecast shown is the latest one published at or before{' '}
              <strong>{formatTimestamp(day.cutoff_utc)} UTC</strong>, the assumed decision time on the
              previous day. The metrics below cover <strong>this day only</strong>, not the whole month.
            </p>
          </div>

          <DayMetrics metrics={day.metrics} />

          {hasAnyData ? (
            <>
              <div className="card">
                <h3>Forecast versus actual generation</h3>
                <p className="muted">
                  Blue is the forecast, orange (dashed) is what was actually generated. Hover over a
                  point for the error and the forecast publication time. A gap in a line means that
                  data is missing.
                </p>
                <ForecastChart rows={day.rows} />
              </div>

              <div className="card">
                <h3>Hourly data</h3>
                <p className="muted">
                  Error = forecast minus actual. A plus sign means the forecast was too high
                  (overforecast), a minus sign means it was too low (underforecast).
                </p>
                <DataTable rows={day.rows} />
              </div>
            </>
          ) : (
            <StatusMessage
              kind="empty"
              title="No data for this day"
              message="Neither an eligible forecast nor actual generation is available for this date, so nothing can be compared. Missing data is never estimated."
            />
          )}
        </>
      )}
    </section>
  )
}

export default ExplorerSection