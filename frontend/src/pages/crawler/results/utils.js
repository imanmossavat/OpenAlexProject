export function formatCentrality(value) {
  if (typeof value !== 'number' || Number.isNaN(value)) return '—'
  if (Math.abs(value) < 0.000001) {
    return value.toExponential(2)
  }
  return value.toFixed(6)
}

export function getAnnotationSwatchClass(mark) {
  switch (mark) {
    case 'good':
      return 'bg-green-500'
    case 'neutral':
      return 'bg-yellow-400'
    case 'bad':
      return 'bg-red-500'
    default:
      return 'bg-gray-300'
  }
}

export function getRowAnnotationClasses(mark) {
  switch (mark) {
    case 'good':
      return 'bg-green-50'
    case 'neutral':
      return 'bg-yellow-50'
    case 'bad':
      return 'bg-red-50/80'
    default:
      return 'bg-white'
  }
}
