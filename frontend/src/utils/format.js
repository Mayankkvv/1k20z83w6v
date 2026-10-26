const oneDecimal = new Intl.NumberFormat('en-GB', {
  minimumFractionDigits: 1,
  maximumFractionDigits: 1,
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
export function formatSignedMw(value) {
  if (isMissing(value)) {
    return NOT_AVAILABLE
  }
  const sign = value > 0 ? '+' : ''
  return `${sign}${oneDecimal.format(value)} MW`
}

export function formatPercent(value) {
  return isMissing(value) ? NOT_AVAILABLE : `${oneDecimal.format(value)}%`
}

export function formatCount(value) {
  return isMissing(value) ? NOT_AVAILABLE : wholeNumber.format(value)
}

// Plain-English names for the data-quality statuses sent by the backend.
export const STATUS_LABELS = {
  missing_forecast: 'hours with no eligible forecast',
  incomplete_actual: 'hours with incomplete actual data (only one half-hour)',
  missing_actual: 'hours with no actual data',
  missing_forecast_and_actual: 'hours with neither forecast nor actual data',
}