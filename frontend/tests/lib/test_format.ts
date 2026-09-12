import { describe, expect, it } from 'vitest'
import { formatMode, formatNullableNumber, formatTimestamp } from '../../src/lib/format'

describe('formatNullableNumber', () => {
  it('renders null as unavailable', () => {
    expect(formatNullableNumber(null, 2)).toBe('Unavailable')
  })

  it.each([
    ['NaN', Number.NaN],
    ['positive infinity', Number.POSITIVE_INFINITY],
    ['negative infinity', Number.NEGATIVE_INFINITY],
  ])('renders %s as unavailable', (_label, value) => {
    expect(formatNullableNumber(value, 2)).toBe('Unavailable')
  })

  it('renders finite values with the requested precision', () => {
    expect(formatNullableNumber(438.2, 1)).toBe('438.2')
    expect(formatNullableNumber(1.926, 2)).toBe('1.93')
  })
})

describe('formatTimestamp', () => {
  it('formats an ISO timestamp for local display', () => {
    const formatted = formatTimestamp('2026-08-23T12:30:15.000Z')

    expect(formatted).not.toBe('Unavailable')
    expect(formatted).toMatch(/2026/)
    expect(formatted).toMatch(/12|30|15/)
  })

  it('renders an invalid timestamp as unavailable', () => {
    expect(formatTimestamp('not-a-timestamp')).toBe('Unavailable')
  })
})

describe('formatMode', () => {
  it.each([
    ['monitor', 'Monitor'],
    ['passive', 'Passive'],
    ['adaptive', 'Adaptive'],
    ['manual', 'Manual'],
  ] as const)('humanizes %s', (mode, expected) => {
    expect(formatMode(mode)).toBe(expected)
  })
})
