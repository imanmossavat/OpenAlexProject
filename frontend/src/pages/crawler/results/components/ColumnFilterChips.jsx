import { Button } from '@/components/ui/button'
import { X } from 'lucide-react'

export default function ColumnFilterChips({ chips, onClearChip, onClearAll }) {
  if (!chips.length) return null

  return (
    <div className="flex flex-wrap items-center gap-2 mb-4">
      {chips.map((chip) => (
        <div
          key={chip.key}
          className="flex items-center gap-2 rounded-full border border-gray-200 bg-white px-3 py-1 text-xs text-gray-700 shadow-sm"
        >
          <span className="font-semibold text-gray-900">{chip.label}:</span>
          <span>{chip.descriptor}</span>
          <button
            type="button"
            className="text-gray-400 hover:text-gray-900 focus-visible:outline-none"
            onClick={() => onClearChip(chip.key)}
            aria-label={`Clear ${chip.label} filters`}
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      ))}
      <Button
        type="button"
        variant="ghost"
        className="rounded-full text-xs text-gray-500 hover:text-gray-900 underline decoration-dotted"
        onClick={onClearAll}
      >
        Clear all column filters
      </Button>
    </div>
  )
}
