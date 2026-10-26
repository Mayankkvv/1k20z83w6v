import MetricCard from './MetricCard.jsx'
import { formatCount, formatMw, formatPercent, formatSignedMw } from '../utils/format.js'

// Cards for the selected day. Each card also shows the whole-month value for comparison.
function DayMetrics({ metrics, monthMetrics }) {
  return (
    <div className="metric-grid">
      <MetricCard
        label="MAE (this day)"
        value={formatMw(metrics.mae_mw)}
        detail={`Whole month: ${formatMw(monthMetrics.mae_mw)}`}
        description="Typical size of the forecast miss on this day."
      />
      <MetricCard
        label="RMSE (this day)"
        value={formatMw(metrics.rmse_mw)}
        detail={`Whole month: ${formatMw(monthMetrics.rmse_mw)}`}
        description="Like MAE, but large misses count more."
      />
      <MetricCard
        label="Mean bias (this day)"
        value={formatSignedMw(metrics.mean_bias_mw)}
        detail={`Whole month: ${formatSignedMw(monthMetrics.mean_bias_mw)}`}
        description={`${formatCount(metrics.overforecast_periods)} hours overforecast, ${formatCount(metrics.underforecast_periods)} underforecast. Positive means the forecast was too high on average.`}
      />
      <MetricCard
        label="MAPE (this day)"
        value={formatPercent(metrics.mape_pct)}
        detail={`Whole month: ${formatPercent(monthMetrics.mape_pct)}`}
        description="Average miss as a share of actual generation."
      />
      <MetricCard
        label="Matched hours"
        value={`${formatCount(metrics.matched_periods)} of ${formatCount(metrics.total_periods)}`}
        description="Hours with both a forecast and complete actual data."
      />
    </div>
  )
}

export default DayMetrics