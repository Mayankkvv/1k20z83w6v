// signDisplay "negative" hides the minus sign when a tiny negative number rounds to zero ("0.0", not "-0.0").
const oneDecimal = new Intl.NumberFormat('en-GB', {
  minimumFractionDigits: 1,
  maximumFractionDigits: 1,
  signDisplay: 'negative',
})
const wholeNumber = new Intl.NumberFormat('en-GB', { maximumFractionDigits: 0 })

export const NOT_AVAILABLE = 'n/a'

function isMissing(value) {
  return value === null || value === undefined || Number.isNaN(value)
}

export function formatMw(value) {
  return isMissing(value) ? NOT_AVAILABLE : `${oneDecimal.format(value)} MW`
}

// Same as formatMw but shows a plus sign for positive numbers (used for errors).
// A number that rounds to 0.0 gets no sign at all.
export function formatSignedMw(value) {
  if (isMissing(value)) {
    return NOT_AVAILABLE
  }
  const sign = Math.round(value * 10) / 10 > 0 ? '+' : ''
  return `${sign}${oneDecimal.format(value)} MW`
}

export function formatPercent(value) {
  return isMissing(value) ? NOT_AVAILABLE : `${oneDecimal.format(value)}%`
}

export function formatCount(value) {
  return isMissing(value) ? NOT_AVAILABLE : wholeNumber.format(value)
}

// "2025-12-31T09:30:00Z" -> "2025-12-31 09:30"
export function formatTimestamp(value) {
  return isMissing(value) ? NOT_AVAILABLE : value.slice(0, 16).replace('T', ' ')
}

// "2026-01-01T07:00:00Z" -> "07:00"
export function formatHour(value) {
  return value.slice(11, 16)
}

// Short labels for the data table.
export const STATUS_SHORT_LABELS = {
  ok: 'OK',
  missing_forecast: 'No eligible forecast',
  incomplete_actual: 'Incomplete actual',
  missing_actual: 'No actual data',
  missing_forecast_and_actual: 'No data',
}

// Plain-English names for the data-quality statuses sent by the backend.
export const STATUS_LABELS = {
  missing_forecast: 'hours with no eligible forecast',
  incomplete_actual: 'hours with incomplete actual data (only one half-hour)',
  missing_actual: 'hours with no actual data',
  missing_forecast_and_actual: 'hours with neither forecast nor actual data',
}