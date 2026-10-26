// Shows a loading, error or empty message. kind is "loading", "error" or "empty".
function StatusMessage({ kind, title, message, actionLabel, onAction }) {
  return (
    <div
      className={`card status status-${kind}`}
      role={kind === 'error' ? 'alert' : 'status'}
    >
      {kind === 'loading' && <div className="spinner" aria-hidden="true" />}
      <div>
        <h2>{title}</h2>
        <p>{message}</p>
        {actionLabel && (
          <button type="button" className="button" onClick={onAction}>
            {actionLabel}
          </button>
        )}
      </div>
    </div>
  )
}

export default StatusMessage