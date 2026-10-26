import { useEffect, useState } from 'react'
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import StatusMessage from './StatusMessage.jsx'
import { getAccuracy } from '../services/api.js'
import { formatCount, formatMw, formatSignedMw } from '../utils/format.js'

const BAR_COLOR = '#8fb3d9'
const SELECTED_BAR_COLOR = 'var(--color-primary-dark)'

function DayTooltip({ active, payload }) {
  if (!active || !payload || payload.length === 0) {
    return null
  }
  const day = payload[0].payload
  return (
    <div className="chart-tooltip">
      <strong>{day.date}</strong>
      <div>MAE: {formatMw(day.mae)}</div>
      <div>Mean bias: {formatSignedMw(day.bias)}</div>
      <div>
        Matched hours: {formatCount(day.matched)} of {formatCount(day.total)}
      </div>
      <div className="muted">Click to open this day below</div>
    </div>
  )
}

// Daily MAE for every day of the month. Clicking a bar (or a "largest errors" button) selects that day.
function AccuracySection({ selectedDate, onSelectDate, monthMae }) {
  const [result, setResult] = useState(null)
  const [reloadKey, setReloadKey] = useState(0)

  useEffect(() => {
    let cancelled = false

    getAccuracy()
      .then((data) => {
        if (!cancelled) {
          setResult({ key: reloadKey, daily: data.daily, error: null })
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setResult({ key: reloadKey, daily: null, error: err.message })
        }
      })

    return () => {
      cancelled = true
    }
  }, [reloadKey])

  const loading = result === null || result.key !== reloadKey

  if (loading) {
    return (
      <StatusMessage
        kind="loading"
        title="Loading daily accuracy"
        message="Calculating forecast error for every day in January."
      />
    )
  }

  if (result.error) {
    return (
      <StatusMessage
        kind="error"
        title="Could not load daily accuracy"
        message={result.error}
        actionLabel="Try again"
        onAction={() => setReloadKey((key) => key + 1)}
      />
    )
  }

  const data = result.daily.map((day) => ({
    date: day.date,
    label: day.date.slice(8),
    mae: day.mae_mw,
    bias: day.mean_bias_mw,
    matched: day.matched_periods,
    total: day.total_periods,
  }))

  const worstDays = data
    .filter((day) => day.mae !== null)
    .sort((a, b) => b.mae - a.mae)
    .slice(0, 3)

  return (
    <section>
      <div className="section-heading">
        <h2>Daily forecast accuracy</h2>
        <p className="muted">
          Mean absolute error (MAE) for each delivery day in January 2026. Taller bars are days
          where the forecast missed by more. Click a bar to open that day in the explorer below.
        </p>
      </div>

      <div className="card">
        <div className="daily-chart">
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={data} margin={{ top: 16, right: 12, bottom: 20, left: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" vertical={false} />
              <XAxis
                dataKey="label"
                interval="preserveStartEnd"
                minTickGap={8}
                tick={{ fontSize: 12 }}
                label={{ value: 'Day of January 2026', position: 'insideBottom', offset: -12, fontSize: 12 }}
              />
              <YAxis
                width={56}
                tick={{ fontSize: 12 }}
                tickFormatter={(value) => value.toLocaleString('en-GB')}
                label={{ value: 'MAE (MW)', angle: -90, position: 'insideLeft', fontSize: 12 }}
              />
              <Tooltip content={<DayTooltip />} cursor={{ fill: 'rgba(11, 92, 173, 0.08)' }} />
              {monthMae !== null && monthMae !== undefined && (
                <ReferenceLine
                  y={monthMae}
                  stroke="var(--color-actual)"
                  strokeDasharray="6 3"
                />
              )}
              <Bar
                dataKey="mae"
                isAnimationActive={false}
                onClick={(_, index) => onSelectDate(data[index].date)}
              >
                {data.map((day) => (
                  <Cell
                    key={day.date}
                    fill={day.date === selectedDate ? SELECTED_BAR_COLOR : BAR_COLOR}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        <p className="chart-key muted">
          <span className="key-line" aria-hidden="true" /> Dashed orange line: January average (
          {formatMw(monthMae)}). <span className="key-bar" aria-hidden="true" /> Dark bar: the day
          shown in the explorer.
        </p>

        {worstDays.length > 0 && (
          <div className="worst-days">
            <h3>Days with the largest forecast errors</h3>
            <div className="worst-days-list">
              {worstDays.map((day) => (
                <button
                  key={day.date}
                  type="button"
                  className="button button-secondary"
                  onClick={() => onSelectDate(day.date)}
                >
                  {day.date}: MAE {formatMw(day.mae)}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </section>
  )
}

export default AccuracySection