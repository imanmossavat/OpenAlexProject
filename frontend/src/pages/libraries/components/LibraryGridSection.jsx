import { Button } from '@/components/ui/button'
import { Loader2 } from 'lucide-react'

import LibraryCard from './LibraryCard'

export default function LibraryGridSection({
  libraries,
  loading,
  error,
  onRetry,
  onSelectLibrary,
  page,
  pageSize,
  totalLibraries,
  onPageChange,
  hasNextPage,
  disabled = false,
}) {
  const hasLibraries = libraries.length > 0
  return (
    <>
      {loading ? (
        <div className="rounded-2xl border border-gray-200 p-10 flex items-center justify-center text-gray-500">
          <Loader2 className="w-5 h-5 animate-spin mr-2" />
          Looking for libraries…
        </div>
      ) : error ? (
        <div className="rounded-2xl border border-red-200 bg-red-50 p-6 text-red-700">
          <p className="font-semibold mb-2">Could not discover libraries</p>
          <p className="text-sm mb-4">{error}</p>
          <Button variant="outline" className="rounded-full" onClick={onRetry}>
            Try again
          </Button>
        </div>
      ) : hasLibraries ? (
        <>
          <div className="grid gap-4 sm:grid-cols-2">
            {libraries.map((library) => (
              <LibraryCard
                key={`${library.path}-${library.name || 'library'}`}
                library={library}
                onSelect={onSelectLibrary}
                disabled={disabled}
              />
            ))}
          </div>
          <div className="flex items-center justify-between pt-2 text-sm text-gray-600">
            <span>
              Showing {(page - 1) * pageSize + 1}- {Math.min(page * pageSize, totalLibraries)} of{' '}
              {totalLibraries} libraries
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
        </>
      ) : (
        <div className="rounded-2xl border border-dashed border-gray-300 p-8 text-center">
          <p className="text-lg font-semibold text-gray-800 mb-2">No libraries discovered</p>
          <p className="text-sm text-gray-500 mb-4">
            Use the custom path section to point us to an existing library folder.
          </p>
        </div>
      )}
    </>
  )
}
