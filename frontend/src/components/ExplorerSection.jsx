import { useEffect, useState } from 'react'
import DataTable from './DataTable.jsx'
import DateSelector from './DateSelector.jsx'
import DayMetrics from './DayMetrics.jsx'
import ForecastChart from './ForecastChart.jsx'
import StatusMessage from './StatusMessage.jsx'
import { getDay } from '../services/api.js'
import { formatTimestamp } from '../utils/format.js'

// The selected date lives in the Dashboard, so the daily accuracy chart can change it too.
function ExplorerSection({ selectedDate, onDateChange, minDate, maxDate, monthMetrics }) {
  // result remembers which request it belongs to, so a slow old answer is never shown for a new date.
  const [result, setResult] = useState(null)
  const [reloadKey, setReloadKey] = useState(0)
  const requestKey = `${selectedDate}#${reloadKey}`

  useEffect(() => {
    let cancelled = false

    getDay(selectedDate)
      .then((data) => {
        if (!cancelled) {
          setResult({ key: requestKey, day: data, error: null })
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setResult({ key: requestKey, day: null, error: err.message })
        }
      })

    return () => {
      cancelled = true
    }
  }, [selectedDate, requestKey])

  const loading = result === null || result.key !== requestKey
  const error = loading ? null : result.error
  const day = loading ? null : result.day

  function handleRetry() {
    setReloadKey((key) => key + 1)
  }

  const hasAnyData = day ? day.rows.some((row) => row.forecast_mw !== null || row.actual_mw !== null) : false

  return (
    <section id="explorer" className="explorer">
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
          minDate={minDate}
          maxDate={maxDate}
          onChange={onDateChange}
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

      {day && (
        <>
          <div className="card day-intro">
            <h3>Delivery date {day.date}</h3>
            <p>
              Each forecast shown is the latest one published at or before{' '}
              <strong>{formatTimestamp(day.cutoff_utc)} UTC</strong>, the assumed decision time on the
              previous day. The metrics below cover <strong>this day only</strong>; the smaller line on
              each card shows the whole-month value for comparison.
            </p>
          </div>

          <DayMetrics metrics={day.metrics} monthMetrics={monthMetrics} />

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