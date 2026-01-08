export function isAbsolutePath(value) {
  if (!value) return false
  const normalized = value.trim()
  if (!normalized) return false
  return normalized.startsWith('/') || /^[a-zA-Z]:[\\/]/.test(normalized)
}

export function deriveNameFromPath(path) {
  if (!path) return 'Library'
  const trimmed = path.replace(/[\\/]+$/, '')
  const segments = trimmed.split(/[\\/]/).filter(Boolean)
  return segments.length ? segments[segments.length - 1] : 'Library'
}
