import { AlertCircle, Loader2, X } from 'lucide-react'

import { Button } from '@/components/ui/button'

import TopicPaperListItem from './TopicPaperListItem'

export default function EntityDrawer({
  visible,
  animating,
  title,
  subtitle,
  error,
  loading,
  papers,
  page,
  total,
  pageSize,
  onClose,
  onPreviousPage,
  onNextPage,
  onSelectPaper,
  canGoPrevious,
  canGoNext,
}) {
  if (!visible) return null

  const startIndex = (page - 1) * pageSize + 1
  const endIndex = Math.min(page * pageSize, total)

  return (
    <div
      className={`fixed inset-0 z-[60] transition-colors duration-300 ${
        animating ? 'pointer-events-auto' : 'pointer-events-none'
      }`}
    >
      <div
        className={`absolute inset-0 bg-black/40 backdrop-blur-[1px] transition-opacity duration-300 ${
          animating ? 'opacity-100' : 'opacity-0'
        }`}
        onClick={animating ? onClose : undefined}
      />
      <div
        className={`absolute inset-y-0 right-0 w-full max-w-3xl bg-white shadow-2xl flex flex-col transform transition-transform duration-300 ease-out ${
          animating ? 'translate-x-0' : 'translate-x-full'
        }`}
        onClick={(event) => event.stopPropagation()}
      >
        <div className="flex items-start justify-between p-6 border-b border-gray-200">
          <div>
            <p className="text-xs uppercase tracking-[0.3em] text-gray-500 mb-1">{title}</p>
            <h3 className="text-2xl font-semibold text-gray-900">{subtitle}</h3>
          </div>
          <button
            type="button"
            className="p-2 rounded-full text-gray-500 hover:bg-gray-100"
            onClick={onClose}
            aria-label="Close"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {error ? (
            <div className="rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-red-700 flex gap-2 items-start">
              <AlertCircle className="w-4 h-4 mt-0.5" />
              <div>{error}</div>
            </div>
          ) : null}
          {loading ? (
            <div className="flex items-center justify-center py-8 text-gray-500">
              <Loader2 className="w-4 h-4 animate-spin mr-2" />
              Loading papers…
            </div>
          ) : papers.length ? (
            papers.map((paper, idx) => (
              <TopicPaperListItem
                key={`${paper.paper_id}-${idx}`}
                paper={paper}
                index={startIndex + idx}
                onSelect={() => onSelectPaper(paper)}
                showCentrality={false}
              />
            ))
          ) : (
            <p className="text-sm text-gray-500">No papers available for this selection.</p>
          )}
        </div>

        <div className="border-t border-gray-200 p-6 flex items-center justify-between">
          <p className="text-sm text-gray-500">
            Showing {total > 0 ? `${startIndex}-${endIndex}` : '0'} of {total} papers
          </p>
          <div className="flex gap-2">
            <Button variant="outline" className="rounded-full" onClick={onPreviousPage} disabled={!canGoPrevious}>
              Previous
            </Button>
            <Button variant="outline" className="rounded-full" onClick={onNextPage} disabled={!canGoNext}>
              Next
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}
