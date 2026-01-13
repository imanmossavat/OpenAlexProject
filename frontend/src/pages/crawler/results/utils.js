export function formatCentrality(value) {
  if (typeof value !== 'number' || Number.isNaN(value)) return '—'
  if (Math.abs(value) < 0.000001) {
    return value.toExponential(2)
  }
  return value.toFixed(6)
}

export function getPreferredPaperUrl(paper) {
  if (!paper) return null
  const rawDoi = typeof paper.doi === 'string' ? paper.doi.trim() : ''
  if (rawDoi) {
    const cleaned = rawDoi.replace(/^https?:\/\/(dx\.)?doi\.org\//i, '')
    if (cleaned) {
      return `https://doi.org/${cleaned}`
    }
  }

  const directUrl = typeof paper.url === 'string' ? paper.url.trim() : ''
  if (directUrl) {
    return directUrl
  }

  const paperId = typeof paper.paper_id === 'string' ? paper.paper_id.trim() : ''
  if (paperId) {
    return `https://openalex.org/${paperId}`
  }
  return null
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

export function downloadTextFile(filename, content) {
  if (typeof window === 'undefined' || !content) return
  const blob = new Blob([content], { type: 'text/plain;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = filename
  document.body.appendChild(anchor)
  anchor.click()
  document.body.removeChild(anchor)
  URL.revokeObjectURL(url)
}
