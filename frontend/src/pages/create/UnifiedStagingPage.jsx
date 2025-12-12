import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import Stepper from '@/components/Stepper'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import apiClient from '@/shared/api/client'
import { endpoints } from '@/shared/api/endpoints'
import { WORKFLOW_STEPS } from './UnifiedStagingPage/constants'
import { useUnifiedSession } from './UnifiedStagingPage/hooks/useUnifiedSession'
import { useUnifiedStagingData } from './UnifiedStagingPage/hooks/useUnifiedStagingData'
import StagingHeader from './UnifiedStagingPage/components/StagingHeader'
import FiltersSidebar from './UnifiedStagingPage/components/FiltersSidebar'
import StagingTable from './UnifiedStagingPage/components/StagingTable'
import ZoteroCollectionsModal from './UnifiedStagingPage/components/ZoteroCollectionsModal'
import PdfUploadModal from './UnifiedStagingPage/components/PdfUploadModal'
import useManualIdImport from './UnifiedStagingPage/hooks/useManualIdImport'
import useZoteroImport from './UnifiedStagingPage/hooks/useZoteroImport'
import usePdfImport from './UnifiedStagingPage/hooks/usePdfImport'

export default function UnifiedStagingPage() {
  const navigate = useNavigate()
  const [showAddMenu, setShowAddMenu] = useState(false)
  const [matching, setMatching] = useState(false)
  const [filtersCollapsed, setFiltersCollapsed] = useState(false)
  const [checkingRetractions, setCheckingRetractions] = useState(false)
  const [retractionSummary, setRetractionSummary] = useState(null)
  const sessionId = useUnifiedSession(navigate)
  const {
    rows,
    loading,
    fetchError,
    setFetchError,
    stats,
    sort,
    setSort,
    page,
    setPage,
    totalPages,
    filters,
    updateFilterField,
    columnFilters,
    columnCustomFilters,
    columnOptions,
    editing,
    activeColumnFilterCount,
    availableSources,
    showInitialEmptyState,
    totalFilteredRows,
    rangeStart,
    rangeEnd,
    fetchRows,
    resetFilters,
    handleColumnFilterApply,
    handleColumnCustomFilterApply,
    clearColumnFilter,
    clearAllColumnFilters,
    toggleSourceFilter,
    startEditing,
    cancelEditing,
    updateEditingValue,
    commitEditing,
    handleSelectRow,
    handleSelectVisible,
    toggleSort,
  } = useUnifiedStagingData({ sessionId })

  const manualImport = useManualIdImport({ sessionId, onSuccess: fetchRows })
  const {
    showZoteroModal,
    closeZoteroModal,
    zoteroCollections,
    selectedCollections,
    setSelectedCollections,
    zoteroLoading,
    zoteroError,
    handleOpenZoteroPicker,
    confirmZoteroImport,
  } = useZoteroImport({ sessionId, navigate, onSuccess: fetchRows })
  const {
    showPdfModal,
    openPdfModal,
    closePdfModal,
    pdfFiles,
    setPdfFiles,
    pdfLoading,
    pdfError,
    grobidStatus,
    confirmPdfUpload,
    navigateToGrobidHelp,
  } = usePdfImport({ sessionId, navigate, onSuccess: fetchRows })

  useEffect(() => {
    if (!stats.totalRows) {
      setRetractionSummary(null)
    }
  }, [stats.totalRows])

  useEffect(() => {
    setRetractionSummary(null)
  }, [sessionId])

  const handleZoteroFromAddMenu = async () => {
    setShowAddMenu(false)
    await handleOpenZoteroPicker()
  }

  const handleOpenManualModal = () => {
    setShowAddMenu(false)
    manualImport.openManualModal()
  }

  const handleOpenPdfUpload = () => {
    setShowAddMenu(false)
    openPdfModal()
  }

  const runMatching = async () => {
    if (!sessionId || !stats.selectedCount) return
    setMatching(true)
    const res = await apiClient('POST', `${endpoints.seedsSession}/${sessionId}/staging/match`, {
      api_provider: 'openalex',
    })
    setMatching(false)
    if (res.error) {
      setFetchError(res.error)
      return
    }
    navigate('/create/staging/matched')
  }

  const handleCheckRetractions = async () => {
    if (!sessionId || !stats.totalRows) return
    setCheckingRetractions(true)
    try {
      const res = await apiClient('POST', `${endpoints.seedsSession}/${sessionId}/staging/retractions/check`)
      if (res.error) {
        setRetractionSummary(null)
        setFetchError(res.error)
        return
      }
      setFetchError(null)
      setRetractionSummary(res.data)
      fetchRows()
    } finally {
      setCheckingRetractions(false)
    }
  }

  const handleSelectedSortToggle = () => {
    setSort((prev) =>
      prev.field === 'selected' ? { field: null, direction: 'asc' } : { field: 'selected', direction: 'desc' }
    )
  }

  return (
    <div className="min-h-screen bg-white flex flex-col">
      <div className="pt-8">
        <Stepper currentStep={2} steps={WORKFLOW_STEPS} />
      </div>

      <div className="px-6 pb-10 flex-1 flex flex-col">
        {!showInitialEmptyState && (
          <StagingHeader
            stats={stats}
            matching={matching}
            onNext={runMatching}
            addSourcesProps={{
              open: showAddMenu,
              onToggle: () => setShowAddMenu((prev) => !prev),
              onManual: handleOpenManualModal,
              onZotero: handleZoteroFromAddMenu,
              onDump: handleOpenPdfUpload,
            }}
          />
        )}

        {showInitialEmptyState ? (
          <div className="flex-1 flex flex-col items-center justify-center text-center px-6 mt-10">
            <div className="max-w-2xl space-y-4">
              <div>
                <p className="text-sm uppercase tracking-[0.3em] text-gray-500 mb-2">No papers staged yet</p>
                <p className="text-2xl font-semibold text-gray-900 mb-3">Bring in papers to get started</p>
                <p className="text-base text-gray-600">
                  Pick one of the options below to import papers from manual IDs, Zotero, or uploaded files.
                </p>
              </div>
              <div className="flex flex-col sm:flex-row gap-3 w-full">
                <Button variant="outline" className="rounded-full flex-1" onClick={manualImport.openManualModal}>
                  Manual IDs
                </Button>
                <Button
                  variant="outline"
                  className="rounded-full flex-1"
                  onClick={handleOpenZoteroPicker}
                >
                  Zotero collections
                </Button>
                <Button variant="outline" className="rounded-full flex-1" onClick={openPdfModal}>
                  Uploaded files
                </Button>
              </div>
            </div>
          </div>
        ) : (
          <div className="mt-6 flex-1 flex overflow-hidden">
            <FiltersSidebar
              filters={filters}
              availableSources={availableSources}
              collapsed={filtersCollapsed}
              activeFilterCount={activeColumnFilterCount}
              onToggleCollapse={() => setFiltersCollapsed((prev) => !prev)}
              onToggleSource={toggleSourceFilter}
              onFilterChange={updateFilterField}
              onReset={resetFilters}
            />
            <StagingTable
              sessionId={sessionId}
              stats={stats}
              rows={rows}
              loading={loading}
              fetchError={fetchError}
              totalFilteredRows={totalFilteredRows}
              rangeStart={rangeStart}
              rangeEnd={rangeEnd}
              sort={sort}
              onToggleSort={toggleSort}
              onRefresh={fetchRows}
              onSelectVisible={handleSelectVisible}
              onToggleSelectedSort={handleSelectedSortToggle}
              activeColumnFilterCount={activeColumnFilterCount}
              columnFilters={columnFilters}
              columnCustomFilters={columnCustomFilters}
              clearColumnFilter={clearColumnFilter}
              clearAllColumnFilters={clearAllColumnFilters}
              columnOptions={columnOptions}
              onApplyColumnFilter={handleColumnFilterApply}
              onApplyCustomColumnFilter={handleColumnCustomFilterApply}
              onSelectRow={handleSelectRow}
              editing={editing}
              onStartEditing={startEditing}
              onChangeEditingValue={updateEditingValue}
              onCommitEditing={commitEditing}
              onCancelEditing={cancelEditing}
              page={page}
              totalPages={totalPages}
              onPreviousPage={() => setPage((p) => Math.max(1, p - 1))}
              onNextPage={() => setPage((p) => Math.min(totalPages, p + 1))}
              onOpenManual={manualImport.openManualModal}
              onOpenZotero={handleOpenZoteroPicker}
              onOpenPdf={openPdfModal}
              onResetFilters={resetFilters}
              onCheckRetractions={handleCheckRetractions}
              checkingRetractions={checkingRetractions}
              retractionSummary={retractionSummary}
            />
          </div>
        )}
      </div>

      <Dialog
        open={manualImport.manualModalOpen}
        onOpenChange={(open) => (open ? manualImport.openManualModal() : manualImport.closeManualModal())}
      >
        <DialogContent className="sm:max-w-2xl bg-white p-0 gap-0 rounded-3xl border-0 shadow-2xl">
          <DialogHeader className="px-6 pt-6 pb-2">
            <DialogTitle>Add manual IDs to staging</DialogTitle>
          </DialogHeader>
          <div className="px-6 pb-6 space-y-4">
            <div>
              <Label className="text-xs uppercase tracking-wider text-gray-500 mb-1 block">Paper IDs</Label>
              <textarea
                className="w-full min-h-[160px] rounded-2xl border border-gray-200 px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-gray-900"
                placeholder="One OpenAlex ID per line (e.g., W2741809807)"
                value={manualImport.manualIds}
                onChange={(e) => manualImport.setManualIds(e.target.value)}
              />
              <p className="text-xs text-gray-500 mt-2">Example: W2741809807</p>
              {manualImport.manualError && <p className="text-sm text-red-600 mt-2">{manualImport.manualError}</p>}
            </div>
            <div className="flex justify-end">
              <Button
                className="rounded-full bg-gray-900 text-white hover:bg-gray-800 disabled:opacity-60"
                onClick={manualImport.addManualRows}
                disabled={manualImport.manualSubmitting}
              >
                {manualImport.manualSubmitting ? 'Adding...' : 'Add to staging'}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      <ZoteroCollectionsModal
        open={showZoteroModal}
        onClose={closeZoteroModal}
        collections={zoteroCollections}
        selected={selectedCollections}
        setSelected={setSelectedCollections}
        loading={zoteroLoading}
        error={zoteroError}
        onOpenSettings={() => navigate('/settings/integrations?provider=zotero')}
        onConfirm={confirmZoteroImport}
      />

      <PdfUploadModal
        open={showPdfModal}
        onClose={closePdfModal}
        files={pdfFiles}
        setFiles={setPdfFiles}
        loading={pdfLoading}
        error={pdfError}
        grobidStatus={grobidStatus}
        onOpenGrobidGuide={navigateToGrobidHelp}
        onConfirm={confirmPdfUpload}
      />
    </div>
  )
}
