import {
  STATUS_SHORT_LABELS,
  formatMw,
  formatSignedMw,
  formatTimestamp,
} from '../utils/format.js'

// Error styling: the sign (+ or -) is always shown too, so colour is never the only clue.
function errorClass(error) {
  if (error === null || error === undefined || error === 0) {
    return ''
  }
  return error > 0 ? 'error-over' : 'error-under'
}

function DataTable({ rows }) {
  return (
    <div className="table-scroll">
      <table className="data-table">
        <caption className="visually-hidden">
          Hourly forecast and actual wind generation for the selected day
        </caption>
        <thead>
          <tr>
            <th scope="col">Delivery hour (UTC)</th>
            <th scope="col" className="num">Forecast</th>
            <th scope="col" className="num">Actual</th>
            <th scope="col" className="num">Error (forecast - actual)</th>
            <th scope="col">Forecast published (UTC)</th>
            <th scope="col">Data status</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.delivery_time} className={row.status === 'ok' ? '' : 'row-warning'}>
              <th scope="row">{row.delivery_time.slice(0, 16).replace('T', ' ')}</th>
              <td className="num">{formatMw(row.forecast_mw)}</td>
              <td className="num">{formatMw(row.actual_mw)}</td>
              <td className={`num ${errorClass(row.error_mw)}`}>{formatSignedMw(row.error_mw)}</td>
              <td>{formatTimestamp(row.forecast_publish_time)}</td>
              <td>
                <span className={`badge ${row.status === 'ok' ? 'badge-ok' : 'badge-warning'}`}>
                  {STATUS_SHORT_LABELS[row.status] || row.status}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default DataTable