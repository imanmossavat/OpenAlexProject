export function parseDate(value) {
  if (!value) return null

  if (value instanceof Date) {
    return Number.isNaN(value.getTime()) ? null : value
  }

  const hasTimezone = /([zZ]|[+-]\d{2}:?\d{2})$/.test(`${value}`)
  const parsed = new Date(value)
  if (Number.isNaN(parsed.getTime())) {
    return null
  }

  if (hasTimezone) {
    return parsed
  }

  // Treat naive timestamps as UTC to avoid browser-local offsets
  return new Date(`${value}Z`)
}

export function formatTimestamp(value) {
  const date = parseDate(value)
  if (!date) return ''
  return date.toLocaleString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export function formatDuration(start, end = new Date()) {
  const startDate = parseDate(start)
  const endDate = parseDate(end)
  if (!startDate || !endDate) return ''
  const diffMs = Math.max(0, endDate.getTime() - startDate.getTime())
  const totalSeconds = Math.floor(diffMs / 1000)
  const hours = Math.floor(totalSeconds / 3600)
  const minutes = Math.floor((totalSeconds % 3600) / 60)
  const seconds = totalSeconds % 60

  if (hours > 0) return `${hours}h ${minutes}m`
  if (minutes > 0) return `${minutes}m ${seconds}s`
  return `${seconds}s`
}
