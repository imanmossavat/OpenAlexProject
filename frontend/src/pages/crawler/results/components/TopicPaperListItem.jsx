import { Button } from '@/components/ui/button'
import { ExternalLink } from 'lucide-react'

import { formatCentrality, getPreferredPaperUrl } from '../utils'

export default function TopicPaperListItem({ paper, index, onSelect, showCentrality = true }) {
  const authors =
    paper.authors && paper.authors.length ? paper.authors.join(', ') : 'Unknown authors'
  const metaParts = [
    paper.year ? `${paper.year}` : null,
    typeof paper.citation_count === 'number' ? `${paper.citation_count} citations` : null,
    paper.venue || null,
  ].filter(Boolean)
  const meta = metaParts.join(' • ')
  const centralityMetrics = paper.centrality_metrics || {}
  const centralityIn =
    typeof centralityMetrics.centrality_in === 'number' ? centralityMetrics.centrality_in : null
  const centralityOut =
    typeof centralityMetrics.centrality_out === 'number' ? centralityMetrics.centrality_out : null

  return (
    <div
      role="button"
      tabIndex={0}
      onClick={onSelect}
      onKeyDown={(event) => {
        if (event.key === 'Enter' || event.key === ' ') {
          event.preventDefault()
          onSelect()
        }
      }}
      className="bg-white border-b border-gray-200 pb-4 hover:bg-gray-50 transition-colors duration-200 cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gray-400"
    >
      <div className="flex items-start gap-4">
        <div className="w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center flex-shrink-0">
          <span className="text-sm font-semibold text-gray-700">{index}</span>
        </div>

        <div className="flex-1 min-w-0">
          <div className="text-lg font-semibold text-gray-900 mb-1 truncate">
            {paper.title || paper.paper_id || 'Untitled paper'}
          </div>

          {paper.abstract ? (
            <div className="text-sm text-gray-600 mb-2 line-clamp-2">{paper.abstract}</div>
          ) : null}

          <div className="text-xs text-gray-500 mb-1">{authors}</div>
          {meta ? <div className="text-xs text-gray-500">{meta}</div> : null}

          {showCentrality ? (
            <div className="space-y-2 mt-3">
              {centralityIn != null && (
                <div>
                  <div className="flex items-center justify-between text-xs text-gray-600 mb-1">
                    <span>Centrality (In)</span>
                    <span className="font-semibold text-gray-700">
                      {formatCentrality(centralityIn)}
                    </span>
                  </div>
                  <div className="w-1/2 bg-gray-200 rounded-full h-1.5 overflow-hidden">
                    <div
                      className="h-full bg-black rounded-full transition-all"
                      style={{ width: `${Math.min(1, Math.max(0, centralityIn)) * 100}%` }}
                    />
                  </div>
                </div>
              )}
              {centralityOut != null && (
                <div>
                  <div className="flex items-center justify-between text-xs text-gray-600 mb-1">
                    <span>Centrality (Out)</span>
                    <span className="font-semibold text-gray-700">
                      {formatCentrality(centralityOut)}
                    </span>
                  </div>
                  <div className="w-1/2 bg-gray-200 rounded-full h-1.5 overflow-hidden">
                    <div
                      className="h-full bg-gray-800 rounded-full transition-all"
                      style={{ width: `${Math.min(1, Math.max(0, centralityOut)) * 100}%` }}
                    />
                  </div>
                </div>
              )}
              {centralityIn == null && centralityOut == null ? (
                <div className="flex items-center gap-3">
                  <span className="text-xs font-semibold text-gray-700">Centrality: N/A</span>
                </div>
              ) : null}
            </div>
          ) : null}
        </div>

        {getPreferredPaperUrl(paper) ? (
          <Button
            variant="outline"
            size="sm"
            className="bg-gray-100 hover:bg-gray-200 border-gray-300 rounded-full flex-shrink-0"
            asChild
            onClick={(event) => event.stopPropagation()}
          >
            <a
              href={getPreferredPaperUrl(paper)}
              target="_blank"
              rel="noreferrer"
              className="flex items-center gap-1 text-xs"
            >
              Source <ExternalLink className="w-3 h-3" />
            </a>
          </Button>
        ) : null}
      </div>
    </div>
  )
}
