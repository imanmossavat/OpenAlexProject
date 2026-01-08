import { FolderOpen } from 'lucide-react'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

import { deriveNameFromPath } from '../utils'

export default function LibraryCard({ library, onSelect, disabled = false }) {
  const { name, path, description, paper_count: paperCount, api_provider: provider } = library
  const handleSelect = () => {
    if (!disabled && onSelect) onSelect(library)
  }

  return (
    <Card
      role="button"
      tabIndex={0}
      onClick={handleSelect}
      onKeyPress={(event) => {
        if (!disabled && (event.key === 'Enter' || event.key === ' ')) {
          event.preventDefault()
          handleSelect()
        }
      }}
      className={`h-full flex flex-col border-gray-200 bg-white shadow-sm rounded-3xl ${
        disabled
          ? 'opacity-60 cursor-not-allowed'
          : 'hover:shadow-lg hover:bg-gray-50 transition duration-200 cursor-pointer'
      }`}
      aria-disabled={disabled}
    >
      <CardHeader className="space-y-3 rounded-t-3xl pointer-events-none">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gray-100 flex items-center justify-center">
            <FolderOpen className="w-5 h-5 text-gray-600" />
          </div>
          <div className="min-w-0">
            <CardTitle className="text-xl leading-tight break-words line-clamp-2">
              {name || deriveNameFromPath(path)}
            </CardTitle>
            <CardDescription className="text-xs uppercase tracking-wide text-gray-500">
              {paperCount ? `${paperCount} paper${paperCount === 1 ? '' : 's'}` : 'Unknown size'}
            </CardDescription>
          </div>
        </div>
        {description ? (
          <p className="text-sm text-gray-600 line-clamp-3">{description}</p>
        ) : (
          <p className="text-sm text-gray-400 italic">No description provided.</p>
        )}
      </CardHeader>
      <CardContent className="flex-1 flex flex-col gap-4 text-sm text-gray-600 rounded-b-3xl">
        <div>
          <p className="text-xs uppercase tracking-wider text-gray-500 mb-1">Location</p>
          <p className="font-mono text-[13px] break-all">{path}</p>
        </div>
        {provider ? (
          <div>
            <p className="text-xs uppercase tracking-wider text-gray-500 mb-1">API provider</p>
            <p>{provider}</p>
          </div>
        ) : null}
      </CardContent>
    </Card>
  )
}
