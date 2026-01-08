import { useMemo, useState } from 'react'
import { Loader2 } from 'lucide-react'

import { deriveNameFromPath, isAbsolutePath } from './utils'
import useLibraryDiscovery from './hooks/useLibraryDiscovery'
import useLibraryRootPreference from './hooks/useLibraryRootPreference'
import useLibraryEditWorkflow from './hooks/useLibraryEditWorkflow'
import LibrarySearchBar from './components/LibrarySearchBar'
import LibraryGridSection from './components/LibraryGridSection'
import DefaultRootPanel from './components/DefaultRootPanel'
import CustomPathPanel from './components/CustomPathPanel'
import ActionErrorAlert from './components/ActionErrorAlert'
import { Button } from '@/components/ui/button'

export default function LibraryEditPage() {
  const {
    libraries,
    loading,
    error: fetchError,
    page,
    total: totalLibraries,
    pageSize,
    hasNextPage,
    searchInput,
    setSearchInput,
    activeQuery,
    goToNextPage,
    clearSearch,
    reload,
  } = useLibraryDiscovery({ pageSize: 8 })
  const {
    defaultRoot,
    rootInput,
    setRootInput,
    rootError,
    rootLoading,
    rootSaving,
    rootPathHasValue,
    rootPathValid,
    saveRoot,
    resetRoot,
    clearRootError,
  } = useLibraryRootPreference()

  const { startEditing, loading: editing, error: actionError, clearError } = useLibraryEditWorkflow()

  const [manualPath, setManualPath] = useState('')
  const [manualError, setManualError] = useState(null)

  const absolutePathValid = useMemo(() => isAbsolutePath(manualPath), [manualPath])

  const handleSelectLibrary = (libraryInfo) => {
    if (!libraryInfo) return
    clearError()
    const payload = {
      path: libraryInfo.path,
      name: libraryInfo.name || deriveNameFromPath(libraryInfo.path),
      description: libraryInfo.description,
    }
    startEditing(payload)
  }

  const handleManualSubmit = () => {
    if (!absolutePathValid) {
      setManualError('Please enter an absolute path.')
      return
    }
    setManualError(null)
    clearError()
    startEditing({
      path: manualPath.trim(),
      name: deriveNameFromPath(manualPath),
    })
  }

  return (
    <div className="min-h-[calc(100vh-160px)] bg-white">
      <div className="max-w-6xl mx-auto px-6 py-12 space-y-10">
        <section>
          <p className="text-xs uppercase tracking-[0.4em] text-gray-500 mb-3">Edit library</p>
          <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
            <div>
              <h1 className="text-4xl font-bold text-gray-900 mb-3">Pick a library to edit</h1>
              <p className="text-gray-600 text-lg max-w-3xl">
                Choose a library to open its papers directly in the staging workspace. From there you can filter,
                add new sources, and decide which papers to keep.
              </p>
            </div>
            <Button variant="outline" className="rounded-full" onClick={reload} disabled={loading}>
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin mr-2" />
                  Refreshing…
                </>
              ) : (
                <>Refresh list</>
              )}
            </Button>
          </div>
        </section>

        <ActionErrorAlert message={actionError} />

        <div className="grid gap-8 lg:grid-cols-3">
          <div className="lg:col-span-2 space-y-4">
            <LibrarySearchBar
              value={searchInput}
              onChange={setSearchInput}
              onClear={clearSearch}
              disabled={!searchInput && !activeQuery}
            />
            <LibraryGridSection
              libraries={libraries}
              loading={loading}
              error={fetchError}
              onRetry={reload}
              onSelectLibrary={handleSelectLibrary}
              page={page}
              pageSize={pageSize}
              totalLibraries={totalLibraries}
              onPageChange={goToNextPage}
              hasNextPage={hasNextPage}
              disabled={editing}
            />
            {editing && (
              <div className="rounded-2xl border border-gray-200 bg-gray-50 p-4 text-sm text-gray-600 flex items-center gap-2">
                <Loader2 className="w-4 h-4 animate-spin" />
                Loading library into staging…
              </div>
            )}
          </div>

          <div className="space-y-6">
            <DefaultRootPanel
              defaultRoot={defaultRoot}
              rootInput={rootInput}
              onChange={(value) => {
                setRootInput(value)
                clearRootError()
              }}
              rootError={rootError}
              rootLoading={rootLoading}
              rootSaving={rootSaving}
              onSave={saveRoot}
              onReset={resetRoot}
              canSave={rootPathHasValue && rootPathValid}
            />
            <CustomPathPanel
              manualPath={manualPath}
              onChange={(value) => {
                setManualPath(value)
                setManualError(null)
              }}
              manualError={manualError}
              onSubmit={handleManualSubmit}
              isValidPath={absolutePathValid}
              disabled={editing}
            />
          </div>
        </div>
      </div>
    </div>
  )
}
