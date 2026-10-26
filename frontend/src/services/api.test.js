import { afterEach, describe, expect, it, vi } from 'vitest'
import { getAccuracy, getDay, getOverview } from './api.js'

// Builds a fake answer like the one the browser's fetch() returns.
function fakeResponse({ ok = true, status = 200, body = {}, jsonFails = false } = {}) {
  return {
    ok,
    status,
    json: jsonFails ? () => Promise.reject(new Error('not json')) : () => Promise.resolve(body),
  }
}

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('api calls', () => {
  it('returns the JSON body when the backend answers normally', async () => {
    const fetchMock = vi.fn().mockResolvedValue(fakeResponse({ body: { period: 'ok' } }))
    vi.stubGlobal('fetch', fetchMock)

    await expect(getOverview()).resolves.toEqual({ period: 'ok' })
    expect(fetchMock.mock.calls[0][0]).toMatch(/\/api\/overview$/)
  })

  it('asks for the right addresses', async () => {
    const fetchMock = vi.fn().mockResolvedValue(fakeResponse())
    vi.stubGlobal('fetch', fetchMock)

    await getAccuracy()
    await getDay('2026-01-28')

    expect(fetchMock.mock.calls[0][0]).toMatch(/\/api\/accuracy$/)
    expect(fetchMock.mock.calls[1][0]).toMatch(/\/api\/day\?date=2026-01-28$/)
  })

  it('shows the backend message when the backend reports a problem', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        fakeResponse({ ok: false, status: 502, body: { detail: 'Could not get data from Elexon: boom' } }),
      ),
    )

    await expect(getOverview()).rejects.toThrow('Could not get data from Elexon: boom')
  })

  it('uses a generic message when the error answer is not JSON', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(fakeResponse({ ok: false, status: 500, jsonFails: true })))

    await expect(getOverview()).rejects.toThrow('HTTP 500')
  })

  it('does not show a validation list as the message', async () => {
    // FastAPI answers 422 with detail as a list, which is not a readable sentence.
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(fakeResponse({ ok: false, status: 422, body: { detail: [{ msg: 'bad' }] } })),
    )

    await expect(getDay('abc')).rejects.toThrow('HTTP 422')
  })

  it('explains when the backend cannot be reached', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('Failed to fetch')))

    await expect(getOverview()).rejects.toThrow('Cannot reach the WindSight backend')
  })
})