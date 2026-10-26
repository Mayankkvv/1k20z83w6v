// Lets the user pick a delivery date between minDate and maxDate (both "YYYY-MM-DD").
function DateSelector({ value, minDate, maxDate, onChange }) {
  // Moves the date by a number of days. Dates are handled as UTC to avoid time-zone surprises.
  function shift(days) {
    const date = new Date(`${value}T00:00:00Z`)
    date.setUTCDate(date.getUTCDate() + days)
    onChange(date.toISOString().slice(0, 10))
  }

  function handleInput(event) {
    const picked = event.target.value
    // The input is empty while the user is typing, so only accept complete dates in range.
    if (picked && picked >= minDate && picked <= maxDate) {
      onChange(picked)
    }
  }

  return (
    <div className="date-selector">
      <button
        type="button"
        className="button button-secondary"
        onClick={() => shift(-1)}
        disabled={value <= minDate}
      >
        Previous day
      </button>
      <label className="date-field">
        <span>Delivery date</span>
        <input
          type="date"
          value={value}
          min={minDate}
          max={maxDate}
          onChange={handleInput}
        />
      </label>
      <button
        type="button"
        className="button button-secondary"
        onClick={() => shift(1)}
        disabled={value >= maxDate}
      >
        Next day
      </button>
    </div>
  )
}

export default DateSelector