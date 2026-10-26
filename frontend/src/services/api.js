// Address of the Python backend. Set VITE_API_BASE_URL in frontend/.env to change it.
const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000').replace(/\/$/, '')

// Calls the backend and returns the JSON answer.
// Throws an Error with a readable message when something goes wrong.
async function getJson(path) {
  let response
  try {
    response = await fetch(`${API_BASE_URL}${path}`)
  } catch {
    throw new Error('Cannot reach the WindSight backend. Check that it is running and try again.')
  }

  if (!response.ok) {
    let message = `The server answered with an error (HTTP ${response.status}).`
    try {
      const body = await response.json()
      if (typeof body.detail === 'string') {
        message = body.detail
      }
    } catch {
      // The error answer was not JSON, so keep the generic message.
    }
    throw new Error(message)
  }

  return response.json()
}

export function getOverview() {
  return getJson('/api/overview')
}