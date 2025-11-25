import { Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import AddSourcesButton from './AddSourcesButton'

export default function StagingHeader({
  stats,
  matching,
  onNext,
  addSourcesProps,
}) {
  return (
    <header className="flex flex-wrap items-center justify-between gap-4 border border-gray-200 rounded-3xl px-6 py-4 bg-white shadow-md">
      <div>
        <p className="text-sm uppercase tracking-[0.3em] text-gray-500 mb-1">Unified staging</p>
        <h1 className="text-2xl font-semibold text-gray-900">
          Review, clean up, filter, and select seeds from any source while spotting retracted papers
        </h1>
      </div>
      <div className="flex items-center gap-2">
        <div className="text-sm text-gray-600 flex flex-col text-right">
          <span>
            <span className="font-semibold text-gray-900">{stats.totalRows}</span> staged •{' '}
            <span className="font-semibold text-gray-900">{stats.selectedCount}</span> selected
          </span>
          {stats.retractedCount ? (
            <span className="text-xs text-red-600 font-medium">{stats.retractedCount} marked retracted</span>
          ) : null}
        </div>
        <AddSourcesButton {...addSourcesProps} />
        <Button
          className="rounded-full bg-gray-900 text-white hover:bg-gray-800 disabled:opacity-60"
          disabled={!stats.selectedCount || matching}
          onClick={onNext}
        >
          {matching ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
          Next
        </Button>
      </div>
    </header>
  )
}
