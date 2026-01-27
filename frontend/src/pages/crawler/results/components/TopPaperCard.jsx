import { Button } from '@/components/ui/button'
import { ExternalLink } from 'lucide-react'

import { formatCentrality, getPreferredPaperUrl } from '../utils'

const OPENALEX_BASE = 'https://openalex.org/'

export default function TopPaperCard({ paper, rank, onSelect, centralityMetric }) {
  const authors =
    paper.authors && paper.authors.length ? paper.authors.join(', ') : 'Unknown authors'
  const metaItems = [
    paper.year ? String(paper.year) : null,
    typeof paper.citation_count === 'number' ? `${paper.citation_count} citations` : null,
    paper.venue || null,
  ].filter(Boolean)
  const meta = metaItems.join(' • ')
  const centralityScore =
    typeof paper.centrality_score === 'number' ? paper.centrality_score : null
  const normalizedCentrality =
    centralityScore != null ? Math.min(1, Math.max(0, centralityScore)) : null
  const centralityMetrics = paper.centrality_metrics || {}
  const centralityIn =
    typeof centralityMetrics.centrality_in === 'number' ? centralityMetrics.centrality_in : null
  const centralityOut =
    typeof centralityMetrics.centrality_out === 'number' ? centralityMetrics.centrality_out : null

  const handleClick = () => {
    if (onSelect) onSelect(paper)
  }

  return (
    <div
      role="button"
      tabIndex={0}
      onClick={handleClick}
      onKeyDown={(event) => {
        if (event.key === 'Enter' || event.key === ' ') {
          event.preventDefault()
          handleClick()
        }
      }}
      className="bg-white border-b border-gray-200 p-6 hover:bg-gray-50 transition-colors duration-200 cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gray-400 rounded-2xl"
    >
      <div className="flex items-start gap-4">
        <div className="w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center flex-shrink-0">
          <span className="text-sm font-semibold text-gray-700">{rank}</span>
        </div>

        <div className="flex-1 min-w-0">
          <div className="text-lg font-semibold text-gray-900 mb-2">
            {paper.title || paper.paper_id || 'Untitled paper'}
          </div>

          {paper.abstract ? (
            <div className="text-sm text-gray-600 mb-2 line-clamp-2">{paper.abstract}</div>
          ) : null}

          <div className="text-sm text-gray-500 mb-1">{authors}</div>
          {meta ? <div className="text-xs text-gray-500">{meta}</div> : null}

          <div className="flex items-center gap-3 mt-3">
            <div className="w-1/2 bg-gray-200 rounded-full h-1.5 overflow-hidden">
              <div
                className="h-full bg-black rounded-full transition-all"
                style={{ width: `${(normalizedCentrality ?? 0) * 100}%` }}
              />
            </div>
            <span className="text-xs font-semibold text-gray-700">
              {centralityScore != null ? formatCentrality(centralityScore) : 'N/A'}
            </span>
          </div>

          {(centralityIn != null || centralityOut != null) && (
            <div className="flex flex-wrap gap-4 text-xs text-gray-600 mt-2">
              {centralityIn != null && (
                <span
                  className={
                    centralityMetric === 'centrality_in' ? 'font-semibold text-gray-900' : undefined
                  }
                >
                  Centrality (In): {formatCentrality(centralityIn)}
                </span>
              )}
              {centralityOut != null && (
                <span
                  className={
                    centralityMetric === 'centrality_out' ? 'font-semibold text-gray-900' : undefined
                  }
                >
                  Centrality (Out): {formatCentrality(centralityOut)}
                </span>
              )}
            </div>
          )}
        </div>

        {getPreferredPaperUrl(paper) ? (
          <Button
            variant="outline"
            size="sm"
            className="bg-gray-100 hover:bg-gray-200 border-gray-300 rounded-full flex-shrink-0"
            asChild
            onClick={(event) => event.stopPropagation()}
          >
            <a href={getPreferredPaperUrl(paper)} target="_blank" rel="noreferrer" className="flex items-center gap-1">
              Source <ExternalLink className="w-3 h-3" />
            </a>
          </Button>
        ) : null}
      </div>
    </div>
  )
}
