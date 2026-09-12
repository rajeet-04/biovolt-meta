const unavailable = 'Unavailable'

export function formatNullableNumber(value: number | null, digits: number): string {
  if (value === null || !Number.isFinite(value)) {
    return unavailable
  }

  return value.toFixed(digits)
}

export function formatTimestamp(value: string): string {
  const timestamp = new Date(value)
  if (Number.isNaN(timestamp.getTime())) {
    return unavailable
  }

  return new Intl.DateTimeFormat(undefined, {
    dateStyle: 'medium',
    timeStyle: 'medium',
  }).format(timestamp)
}

export function formatMode(mode: 'monitor' | 'passive' | 'adaptive' | 'manual'): string {
  return mode.charAt(0).toUpperCase() + mode.slice(1)
}
