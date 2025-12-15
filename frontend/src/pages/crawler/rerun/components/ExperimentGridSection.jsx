import { CalendarClock, Play, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'

function ExperimentCard({ experiment, onSelect }) {
  const title = experiment.display_name || experiment.name || experiment.job_id
  const subtitle = experiment.display_name ? experiment.name : null
  const updated = experiment.updated_at ? new Date(experiment.updated_at) : null

  return (
    <div
      role="button"
      tabIndex={0}
      onClick={() => onSelect(experiment)}
      onKeyDown={(event) => {
        if (event.key === 'Enter' || event.key === ' ') {
          event.preventDefault()
          onSelect(experiment)
        }
      }}
      className="h-full rounded-3xl border border-gray-200 bg-white shadow-sm p-5 flex flex-col gap-4 cursor-pointer hover:shadow-lg hover:bg-gray-50 transition"
    >
      <div className="space-y-1">
        <p className="text-xs uppercase tracking-[0.3em] text-gray-400">Experiment</p>
        <h3 className="text-xl font-semibold text-gray-900 line-clamp-2">{title}</h3>
        {subtitle ? <p className="text-sm text-gray-500 line-clamp-1">{subtitle}</p> : null}
      </div>

      <div className="text-sm text-gray-600 space-y-2 flex-1">
        <p>
          <span className="font-semibold">{experiment.total_seeds}</span> seeds ·{' '}
          <span className="font-semibold">{experiment.total_keywords}</span> keywords
        </p>
        <p className="flex items-center gap-2 text-xs text-gray-500">
          <CalendarClock className="w-4 h-4 text-gray-400" />
          {updated ? updated.toLocaleString() : 'Unknown'}
        </p>
        {experiment.library_path ? (
          <div className="text-xs text-gray-500">
            <p className="text-[11px] uppercase tracking-wide text-gray-400 mb-1">Location</p>
            <p className="font-mono text-[11px] break-all">{experiment.library_path}</p>
            {experiment.library_name ? (
              <p className="text-[11px] text-gray-600 mt-1">Library: {experiment.library_name}</p>
            ) : null}
          </div>
        ) : null}
      </div>

      <div className="flex items-center justify-between text-xs uppercase tracking-wide text-gray-500">
        <span>Tap to re-run</span>
        <Play className="w-4 h-4 text-gray-400" />
      </div>
    </div>
  )
}

export default function ExperimentGridSection({
  experiments,
  loading,
  error,
  page,
  pageSize,
  total,
  hasNextPage,
  onPageChange,
  onRetry,
  onSelectExperiment,
}) {
  if (loading) {
    return (
      <div className="rounded-2xl border border-gray-200 p-10 flex items-center justify-center text-gray-500">
        <Loader2 className="w-5 h-5 animate-spin mr-2" />
        Looking for experiments…
      </div>
    )
  }
  if (error) {
    return (
      <div className="rounded-2xl border border-red-200 bg-red-50 p-6 text-red-700">
        <p className="font-semibold mb-2">Could not load experiments</p>
        <p className="text-sm mb-4">{error}</p>
        <Button variant="outline" className="rounded-full" onClick={onRetry}>
          Try again
        </Button>
      </div>
    )
  }
  if (!experiments.length) {
    return (
      <div className="rounded-2xl border border-dashed border-gray-300 p-8 text-center text-sm text-gray-500">
        No experiments found.
      </div>
    )
  }

  const startIndex = (page - 1) * pageSize
  const endIndex = Math.min(total, startIndex + pageSize)

  return (
    <div className="space-y-4">
      <div className="grid gap-4 sm:grid-cols-2">
        {experiments.map((experiment) => (
          <ExperimentCard key={experiment.job_id} experiment={experiment} onSelect={onSelectExperiment} />
        ))}
      </div>
      <div className="flex items-center justify-between text-sm text-gray-600">
        <span>
          Showing {(page - 1) * pageSize + 1}- {Math.min(page * pageSize, total)} of {total} experiments
        </span>
        <div className="flex gap-2">
          <Button
            variant="outline"
            className="rounded-full"
            onClick={() => onPageChange(-1)}
            disabled={page === 1 || loading}
          >
            Previous
          </Button>
          <Button
            variant="outline"
            className="rounded-full"
            onClick={() => onPageChange(1)}
            disabled={!hasNextPage || loading}
          >
            Next
          </Button>
        </div>
      </div>
    </div>
  )
}
