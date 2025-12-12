import { ChevronDown } from 'lucide-react'
import { Button } from '@/components/ui/button'

export default function AddSourcesButton({ open, onToggle, onManual, onZotero, onDump }) {
  return (
    <div className="relative">
      <Button
        variant="ghost"
        className="rounded-full text-white hover:opacity-90"
        style={{ backgroundColor: 'oklch(37.3% 0.034 259.733)' }}
        onClick={onToggle}
      >
        Add more sources
        <ChevronDown className="w-4 h-4 ml-2" />
      </Button>
      {open && (
        <div className="absolute right-0 mt-2 w-56 rounded-2xl border border-gray-200 bg-white shadow-lg z-20">
          <button
            type="button"
            className="w-full text-left px-4 py-3 text-sm hover:bg-gray-50"
            onClick={onManual}
          >
            Manual IDs
            <p className="text-xs text-gray-500">Paste OpenAlex IDs (one per line)</p>
          </button>
          <button
            type="button"
            className="w-full text-left px-4 py-3 text-sm hover:bg-gray-50"
            onClick={onZotero}
          >
            Zotero collections
            <p className="text-xs text-gray-500">Pick items from your Zotero library</p>
          </button>
          <button
            type="button"
            className="w-full text-left px-4 py-3 text-sm hover:bg-gray-50 rounded-b-2xl"
            onClick={onDump}
          >
            Uploaded files
            <p className="text-xs text-gray-500">Upload one or more document files</p>
          </button>
        </div>
      )}
    </div>
  )
}
