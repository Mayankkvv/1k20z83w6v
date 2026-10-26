import MetricCard from './MetricCard.jsx'
import {
  STATUS_LABELS,
  formatCount,
  formatMw,
  formatPercent,
  formatSignedMw,
} from '../utils/format.js'

function biasMeaning(bias) {
  if (bias === null || bias === undefined) {
    return 'No periods could be compared.'
  }
  if (bias > 0) {
    return 'Positive: on average the forecasts were higher than the actual generation (overforecasting).'
  }
  if (bias < 0) {
    return 'Negative: on average the forecasts were lower than the actual generation (underforecasting).'
  }
  return 'Zero: over- and underforecasts cancelled out.'
}

function dataQualityText(statusCounts) {
  const problems = Object.entries(statusCounts)
    .filter(([status, count]) => status !== 'ok' && count > 0)
    .map(([status, count]) => `${formatCount(count)} ${STATUS_LABELS[status] || status}`)

  if (problems.length === 0) {
    return 'Every hour in the month has an eligible forecast and complete actual data.'
  }
  return `Not compared: ${problems.join('; ')}. Missing data is never estimated.`
}

function OverviewSection({ overview }) {
  const { metrics, assumption, period } = overview

  return (
    <section>
      <div className="section-heading">
        <h2>January 2026 overview</h2>
        <p className="muted">
          These numbers cover the <strong>entire month</strong> (delivery dates {period.start} to{' '}
          {period.end}). Forecast error = forecast minus actual, in megawatts (MW).
        </p>
      </div>

      <div className="metric-grid">
        <MetricCard
          label="Mean absolute error (MAE)"
          value={formatMw(metrics.mae_mw)}
          description="The typical size of a forecast miss, ignoring direction. Lower is better."
        />
        <MetricCard
          label="Root mean squared error (RMSE)"
          value={formatMw(metrics.rmse_mw)}
          description="Like MAE, but big misses count more. A large gap between RMSE and MAE means a few hours were missed badly."
        />
        <MetricCard
          label="Mean bias error"
          value={formatSignedMw(metrics.mean_bias_mw)}
          detail={`${formatCount(metrics.overforecast_periods)} hours overforecast, ${formatCount(metrics.underforecast_periods)} underforecast`}
          description={biasMeaning(metrics.mean_bias_mw)}
        />
        <MetricCard
          label="Mean absolute percentage error (MAPE)"
          value={formatPercent(metrics.mape_pct)}
          description={`The average miss as a share of actual generation. It can look inflated when actual output is low, so hours below ${assumption.mape_min_actual_mw} MW are left out of this one measure (${formatCount(metrics.mape_periods)} hours used).`}
        />
        <MetricCard
          label="Matched hourly periods"
          value={`${formatCount(metrics.matched_periods)} of ${formatCount(metrics.total_periods)}`}
          description="Hours that have both an eligible forecast and complete actual data."
        />
        <MetricCard
          label="Forecast data coverage"
          value={formatPercent(metrics.coverage_pct)}
          description={dataQualityText(metrics.status_counts)}
        />
      </div>

      <div className="card assumption">
        <h3>How the forecast is chosen</h3>
        <p>{assumption.summary}</p>
        <p className="muted">{assumption.note}</p>
      </div>
    </section>
  )
}

export default OverviewSection