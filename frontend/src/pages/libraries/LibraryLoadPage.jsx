import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Loader2 } from 'lucide-react'

import { setSessionId } from '@/shared/lib/session'
import { Button } from '@/components/ui/button'
import apiClient from '@/shared/api/client'
import { endpoints } from '@/shared/api/endpoints'

import useLibraryDiscovery from './hooks/useLibraryDiscovery'
import useLibraryRootPreference from './hooks/useLibraryRootPreference'
import LibrarySearchBar from './components/LibrarySearchBar'
import LibraryGridSection from './components/LibraryGridSection'
import DefaultRootPanel from './components/DefaultRootPanel'
import CustomPathPanel from './components/CustomPathPanel'
import UseCaseDialog from './components/UseCaseDialog'
import LatestSelectionAlert from './components/LatestSelectionAlert'
import ActionErrorAlert from './components/ActionErrorAlert'
import { deriveNameFromPath, isAbsolutePath } from './utils'

const USE_CASES = [
  {
    id: 'crawler_wizard',
    title: 'Crawler workflow',
    description: 'Attach this library to the crawler workflow to collect related papers.',
    nextPath: '/crawler/keywords',
  },
]

export default function LibraryLoadPage() {
  const navigate = useNavigate()
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
  const [manualPath, setManualPath] = useState('')
  const [manualError, setManualError] = useState(null)
  const [pendingLibrary, setPendingLibrary] = useState(null)
  const [useCaseDialogOpen, setUseCaseDialogOpen] = useState(false)
  const [actionError, setActionError] = useState(null)
  const [selecting, setSelecting] = useState(false)
  const [latestSelection, setLatestSelection] = useState(null)

  const absolutePathValid = useMemo(() => isAbsolutePath(manualPath), [manualPath])

  const handleUseCaseRequest = (libraryInfo) => {
    setPendingLibrary(libraryInfo)
    setUseCaseDialogOpen(true)
    setActionError(null)
  }

  const handleManualSubmit = () => {
    if (!absolutePathValid) {
      setManualError('Please enter an absolute path.')
      return
    }
    setManualError(null)
    handleUseCaseRequest({
      name: deriveNameFromPath(manualPath),
      path: manualPath.trim(),
      description: '',
    })
  }

  const handleUseCaseSelection = async (useCase) => {
    if (!pendingLibrary) return
    setSelecting(true)
    setActionError(null)
    try {
      const startRes = await apiClient('POST', `${endpoints.seedsSession}/start`, { use_case: useCase.id })
      if (startRes.error || !startRes.data?.session_id) throw new Error(startRes.error || 'Unable to start session')

      const sessionId = startRes.data.session_id
      setSessionId(sessionId)

      const payload = {
        path: pendingLibrary.path,
        name: pendingLibrary.name,
      }
      const selectRes = await apiClient('POST', `${endpoints.library}/${sessionId}/select`, payload)
      if (selectRes.error || !selectRes.data) throw new Error(selectRes.error || 'Failed to attach library')

      setLatestSelection({
        sessionId,
        libraryName: selectRes.data.name || pendingLibrary.name,
        libraryPath: selectRes.data.path || pendingLibrary.path,
        paperCount: selectRes.data.paper_count ?? null,
        useCase,
        nextPath: useCase.nextPath || null,
      })
      setUseCaseDialogOpen(false)
      setPendingLibrary(null)
      if (useCase.nextPath) {
        navigate(useCase.nextPath)
      }
    } catch (err) {
      setActionError(err.message || 'Something went wrong.')
    } finally {
      setSelecting(false)
    }
  }

  return (
    <div className="min-h-[calc(100vh-160px)] bg-white">
      <div className="max-w-6xl mx-auto px-6 py-12 space-y-10">
        <section>
          <p className="text-xs uppercase tracking-[0.4em] text-gray-500 mb-3">Load library</p>
          <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
            <div>
              <h1 className="text-4xl font-bold text-gray-900 mb-3">Browse your saved libraries</h1>
              <p className="text-gray-600 text-lg max-w-3xl">
                Pick one of the discovered libraries or point to a custom folder. Use the search field to narrow down results.
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

        <LatestSelectionAlert latestSelection={latestSelection} onContinue={navigate} />
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
              onSelectLibrary={handleUseCaseRequest}
              page={page}
              pageSize={pageSize}
              totalLibraries={totalLibraries}
              onPageChange={goToNextPage}
              hasNextPage={hasNextPage}
            />
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
              onChange={setManualPath}
              manualError={manualError}
              onSubmit={handleManualSubmit}
              isValidPath={absolutePathValid}
            />
          </div>
        </div>
      </div>

      <UseCaseDialog
        open={useCaseDialogOpen}
        pendingLibrary={pendingLibrary}
        useCases={USE_CASES}
        onSelect={handleUseCaseSelection}
        selecting={selecting}
        onOpenChange={(open) => !selecting && setUseCaseDialogOpen(open)}
      />
    </div>
  )
}
