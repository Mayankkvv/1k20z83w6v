import { describe, expect, it } from 'vitest'
import {
  NOT_AVAILABLE,
  formatCount,
  formatHour,
  formatMw,
  formatPercent,
  formatSignedMw,
  formatTimestamp,
} from './format.js'

describe('formatMw', () => {
  it('uses one decimal and a thousands separator', () => {
    expect(formatMw(2122.81)).toBe('2,122.8 MW')
    expect(formatMw(13814.5)).toBe('13,814.5 MW')
  })

  it('shows n/a for missing values', () => {
    expect(formatMw(null)).toBe(NOT_AVAILABLE)
    expect(formatMw(undefined)).toBe(NOT_AVAILABLE)
    expect(formatMw(Number.NaN)).toBe(NOT_AVAILABLE)
  })

  it('shows zero as a real value, not as missing', () => {
    expect(formatMw(0)).toBe('0.0 MW')
  })
})

describe('formatSignedMw', () => {
  it('adds a plus sign to overforecasts and keeps the minus sign on underforecasts', () => {
    expect(formatSignedMw(5651.5)).toBe('+5,651.5 MW')
    expect(formatSignedMw(-12.04)).toBe('-12.0 MW')
  })

  it('shows no sign when the value rounds to zero', () => {
    expect(formatSignedMw(0)).toBe('0.0 MW')
    expect(formatSignedMw(0.04)).toBe('0.0 MW')
    expect(formatSignedMw(-0.04)).toBe('0.0 MW')
  })

  it('shows n/a for missing values', () => {
    expect(formatSignedMw(null)).toBe(NOT_AVAILABLE)
  })
})

describe('formatPercent and formatCount', () => {
  it('formats percentages with one decimal', () => {
    expect(formatPercent(22.06)).toBe('22.1%')
    expect(formatPercent(100)).toBe('100.0%')
    expect(formatPercent(null)).toBe(NOT_AVAILABLE)
  })

  it('formats counts as whole numbers', () => {
    expect(formatCount(744)).toBe('744')
    expect(formatCount(1488)).toBe('1,488')
    expect(formatCount(null)).toBe(NOT_AVAILABLE)
  })
})

describe('timestamps', () => {
  it('shortens an ISO timestamp for display', () => {
    expect(formatTimestamp('2025-12-31T09:30:00Z')).toBe('2025-12-31 09:30')
    expect(formatTimestamp(null)).toBe(NOT_AVAILABLE)
  })

  it('extracts the hour for chart labels', () => {
    expect(formatHour('2026-01-01T07:00:00Z')).toBe('07:00')
  })
})