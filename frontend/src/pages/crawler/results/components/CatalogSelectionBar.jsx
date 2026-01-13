import { Button } from '@/components/ui/button'
import { Loader2 } from 'lucide-react'

export default function CatalogSelectionBar({
  selectionCount,
  onClearSelection,
  annotationMarks,
  onBulkMark,
  bulkMarkState,
  onCopySelected,
  copyingSelections,
  onDownloadSelected,
  downloadingSelections,
}) {
  if (selectionCount <= 0) return null
  return (
    <div className="mb-4 flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-blue-100 bg-blue-50 px-4 py-3 text-sm text-blue-900">
      <div className="flex items-center gap-3">
        <span className="font-semibold">{selectionCount} selected</span>
        <Button
          type="button"
          variant="ghost"
          className="rounded-full text-xs text-blue-700 hover:text-blue-900"
          onClick={onClearSelection}
        >
          Clear selection
        </Button>
      </div>
      <div className="flex flex-wrap items-center gap-3">
        <div className="flex flex-wrap gap-2">
          <Button
            type="button"
            variant="outline"
            className="rounded-full text-xs shadow-sm"
            onClick={onCopySelected}
            disabled={copyingSelections}
          >
            {copyingSelections ? <Loader2 className="w-3.5 h-3.5 mr-2 animate-spin" /> : null}
            Copy selected URLs
          </Button>
          <Button
            type="button"
            variant="outline"
            className="rounded-full text-xs shadow-sm"
            onClick={onDownloadSelected}
            disabled={downloadingSelections}
          >
            {downloadingSelections ? <Loader2 className="w-3.5 h-3.5 mr-2 animate-spin" /> : null}
            Download TXT
          </Button>
        </div>
        <div className="flex flex-wrap gap-2 border-l border-blue-200 pl-3">
          {annotationMarks.map((mark) => (
            <Button
              key={`bulk-${mark.value}`}
              type="button"
              variant="outline"
              className="rounded-full text-xs shadow-sm"
              onClick={() => onBulkMark(mark.value)}
              disabled={bulkMarkState.loading}
            >
              {bulkMarkState.loading && bulkMarkState.mark === mark.value ? (
                <Loader2 className="w-3.5 h-3.5 mr-2 animate-spin" />
              ) : null}
              {mark.label}
            </Button>
          ))}
        </div>
      </div>
    </div>
  )
}
