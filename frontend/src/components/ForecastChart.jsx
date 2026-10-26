import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import {
  formatHour,
  formatMw,
  formatSignedMw,
  formatTimestamp,
} from '../utils/format.js'

// The box that appears when the mouse is over the chart.
function ChartTooltip({ active, payload }) {
  if (!active || !payload || payload.length === 0) {
    return null
  }
  const row = payload[0].payload
  return (
    <div className="chart-tooltip">
      <strong>{row.timeLabel} UTC</strong>
      <div>Forecast: {formatMw(row.forecast)}</div>
      <div>Actual: {formatMw(row.actual)}</div>
      <div>Error: {formatSignedMw(row.error)}</div>
      <div className="muted">Forecast published: {formatTimestamp(row.published)} UTC</div>
    </div>
  )
}

function ForecastChart({ rows }) {
  // Missing values stay null, so the line has a visible gap instead of an invented value.
  const data = rows.map((row) => ({
    timeLabel: formatHour(row.delivery_time),
    forecast: row.forecast_mw,
    actual: row.actual_mw,
    error: row.error_mw,
    published: row.forecast_publish_time,
  }))

  return (
    <div className="chart-wrapper">
      <ResponsiveContainer width="100%" height={340}>
        <LineChart data={data} margin={{ top: 8, right: 12, bottom: 20, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
          <XAxis
            dataKey="timeLabel"
            interval="preserveStartEnd"
            minTickGap={28}
            tick={{ fontSize: 12 }}
            label={{ value: 'Delivery hour (UTC)', position: 'insideBottom', offset: -12, fontSize: 12 }}
          />
          <YAxis
            domain={[0, 'auto']}
            width={56}
            tick={{ fontSize: 12 }}
            tickFormatter={(value) => value.toLocaleString('en-GB')}
            label={{ value: 'MW', angle: -90, position: 'insideLeft', fontSize: 12 }}
          />
          <Tooltip content={<ChartTooltip />} />
          <Legend verticalAlign="top" height={36} />
          <Line
            type="monotone"
            dataKey="forecast"
            name="Forecast"
            stroke="var(--color-forecast)"
            strokeWidth={2.5}
            dot={{ r: 3 }}
            connectNulls={false}
            isAnimationActive={false}
          />
          <Line
            type="monotone"
            dataKey="actual"
            name="Actual"
            stroke="var(--color-actual)"
            strokeWidth={2.5}
            strokeDasharray="6 3"
            dot={{ r: 3 }}
            connectNulls={false}
            isAnimationActive={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}

export default ForecastChart