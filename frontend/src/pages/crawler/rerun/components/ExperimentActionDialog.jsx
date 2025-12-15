import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Loader2, PenLine, Repeat } from 'lucide-react'

export default function ExperimentActionDialog({
  open,
  onOpenChange,
  experiment,
  onRerunNow,
  onRerunWithEdits,
  loadingAction,
  error,
}) {
  if (!experiment) return null
  const title = experiment.display_name || experiment.name || experiment.job_id

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg bg-white border border-gray-100">
        <DialogHeader>
          <DialogTitle>Rerun "{title}"</DialogTitle>
          <DialogDescription>
            Choose how you want to reuse this configuration. You can launch a new crawl immediately or preload the wizard
            to make adjustments first.
          </DialogDescription>
          {experiment.manualPath ? (
            <p className="text-xs text-gray-500 break-all mt-2">
              Path: <span className="font-mono">{experiment.manualPath}</span>
            </p>
          ) : null}
        </DialogHeader>
        {error ? <p className="text-sm text-red-600">{error}</p> : null}
        <div className="space-y-3">
          <button
            className="w-full rounded-2xl border border-gray-200 p-4 text-left hover:border-gray-500 hover:shadow-lg transition"
            onClick={onRerunNow}
            disabled={loadingAction}
          >
            <div className="flex items-center gap-3">
              {loadingAction === 'now' ? (
                <Loader2 className="w-5 h-5 animate-spin text-gray-700" />
              ) : (
                <Repeat className="w-5 h-5 text-gray-600" />
              )}
              <div>
                <p className="font-semibold text-gray-900">Re-run now</p>
                <p className="text-sm text-gray-600">Launch a crawler job with the saved settings.</p>
              </div>
            </div>
          </button>
          <button
            className="w-full rounded-2xl border border-gray-200 p-4 text-left hover:border-gray-500 hover:shadow-lg transition"
            onClick={onRerunWithEdits}
            disabled={loadingAction}
          >
            <div className="flex items-center gap-3">
              {loadingAction === 'edit' ? (
                <Loader2 className="w-5 h-5 animate-spin text-gray-700" />
              ) : (
                <PenLine className="w-5 h-5 text-gray-600" />
              )}
              <div>
                <p className="font-semibold text-gray-900">Re-run with edits</p>
                <p className="text-sm text-gray-600">Load this configuration into the crawler wizard.</p>
              </div>
            </div>
          </button>
        </div>
      </DialogContent>
    </Dialog>
  )
}
