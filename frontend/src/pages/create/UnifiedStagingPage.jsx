import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import Stepper from '@/components/Stepper'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import apiClient from '@/shared/api/client'
import { endpoints } from '@/shared/api/endpoints'
import {
  DEFAULT_GROBID_STATUS,
  WORKFLOW_STEPS,
} from './UnifiedStagingPage/constants'
import { useUnifiedSession } from './UnifiedStagingPage/hooks/useUnifiedSession'
import { useUnifiedStagingData } from './UnifiedStagingPage/hooks/useUnifiedStagingData'
import StagingHeader from './UnifiedStagingPage/components/StagingHeader'
import FiltersSidebar from './UnifiedStagingPage/components/FiltersSidebar'
import StagingTable from './UnifiedStagingPage/components/StagingTable'
import ZoteroCollectionsModal from './UnifiedStagingPage/components/ZoteroCollectionsModal'
import PdfUploadModal from './UnifiedStagingPage/components/PdfUploadModal'

export default function UnifiedStagingPage() {
  const navigate = useNavigate()
  const [showAddMenu, setShowAddMenu] = useState(false)
  const [manualModalOpen, setManualModalOpen] = useState(false)
  const [manualIds, setManualIds] = useState('')
  const [manualSubmitting, setManualSubmitting] = useState(false)
  const [manualError, setManualError] = useState(null)
  const [showZoteroModal, setShowZoteroModal] = useState(false)
  const [zoteroCollections, setZoteroCollections] = useState([])
  const [selectedCollections, setSelectedCollections] = useState({})
  const [zoteroLoading, setZoteroLoading] = useState(false)
  const [zoteroError, setZoteroError] = useState(null)
  const [showPdfModal, setShowPdfModal] = useState(false)
  const [pdfFiles, setPdfFiles] = useState([])
  const [pdfLoading, setPdfLoading] = useState(false)
  const [pdfError, setPdfError] = useState(null)
  const [grobidStatus, setGrobidStatus] = useState(DEFAULT_GROBID_STATUS)
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

  useEffect(() => {
    if (!showZoteroModal) return
    const loadCollections = async () => {
      if (!sessionId) return
      setZoteroError(null)
      const res = await apiClient('GET', `${endpoints.seedsSession}/${sessionId}/zotero/collections`)
      if (res.error) {
        setZoteroError(res.error)
      } else {
        setZoteroCollections(res.data?.collections || [])
        const defaults = {}
        ;(res.data?.collections || []).forEach((c) => {
          defaults[c.key] = false
        })
        setSelectedCollections((prev) => ({ ...defaults, ...prev }))
      }
    }
    loadCollections()
  }, [showZoteroModal, sessionId])

  useEffect(() => {
    if (!showPdfModal || !sessionId) return
    let isCancelled = false
    setGrobidStatus(DEFAULT_GROBID_STATUS)
    const checkGrobid = async () => {
      const res = await apiClient('GET', `${endpoints.seedsSession}/${sessionId}/pdfs/grobid/status`)
      if (isCancelled) return
      if (res.error) {
        setGrobidStatus({ checked: true, available: false, message: res.error })
        return
      }
      const available = Boolean(res.data?.available)
      setGrobidStatus({
        checked: true,
        available,
        message:
          res.data?.message ||
          (available
            ? null
            : 'GROBID service is not running. Please start it before uploading PDF files.'),
      })
    }
    checkGrobid()
    return () => {
      isCancelled = true
    }
  }, [showPdfModal, sessionId])

  useEffect(() => {
    if (!stats.totalRows) {
      setRetractionSummary(null)
    }
  }, [stats.totalRows])

  useEffect(() => {
    setRetractionSummary(null)
  }, [sessionId])

  const openManualModal = () => {
    setManualModalOpen(true)
    setManualError(null)
  }

  const handleOpenZoteroPicker = async () => {
    setShowAddMenu(false)
    if (!sessionId) return
    setZoteroError(null)
    const availability = await apiClient('GET', `${endpoints.seedsSession}/${sessionId}/zotero/availability`)
    if (availability.error) {
      setZoteroError(availability.error)
      return
    }
    if (availability.data?.available) {
      setShowZoteroModal(true)
    } else {
      setZoteroError(availability.data?.message || 'Zotero is not configured yet.')
      navigate('/settings/integrations?provider=zotero')
    }
  }

  const prepareManualPayload = () => {
    const ids = manualIds
      .split(/\r?\n/)
      .map((s) => s.trim())
      .filter(Boolean)
    return ids.map((value) => {
      const doi = normalizeDoi(value)
      return {
        source: 'Manual IDs',
        source_type: 'manual',
        source_id: value,
        doi,
        is_selected: false,
      }
    })
  }

  const addManualRows = async () => {
    if (!sessionId) return
    const payload = prepareManualPayload()
    if (!payload.length) {
      setManualError('Enter at least one ID')
      return
    }
    setManualSubmitting(true)
    const res = await apiClient('POST', `${endpoints.seedsSession}/${sessionId}/staging`, payload)
    setManualSubmitting(false)
    if (res.error) {
      setManualError(res.error)
    } else {
      setManualIds('')
      setManualModalOpen(false)
      fetchRows()
    }
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
              onManual: () => {
                openManualModal()
                setShowAddMenu(false)
              },
              onZotero: handleOpenZoteroPicker,
              onDump: () => {
                setShowAddMenu(false)
                setShowPdfModal(true)
              },
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
                <Button variant="outline" className="rounded-full flex-1" onClick={openManualModal}>
                  Manual IDs
                </Button>
                <Button
                  variant="outline"
                  className="rounded-full flex-1"
                  onClick={() => {
                    setShowZoteroModal(true)
                    setZoteroError(null)
                  }}
                >
                  Zotero collections
                </Button>
                <Button variant="outline" className="rounded-full flex-1" onClick={() => setShowPdfModal(true)}>
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
              onOpenManual={openManualModal}
              onOpenZotero={() => {
                setShowZoteroModal(true)
                setZoteroError(null)
              }}
              onOpenPdf={() => setShowPdfModal(true)}
              onResetFilters={resetFilters}
              onCheckRetractions={handleCheckRetractions}
              checkingRetractions={checkingRetractions}
              retractionSummary={retractionSummary}
            />
          </div>
        )}
      </div>

      <Dialog open={manualModalOpen} onOpenChange={setManualModalOpen}>
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
                value={manualIds}
                onChange={(e) => setManualIds(e.target.value)}
              />
              <p className="text-xs text-gray-500 mt-2">Example: W2741809807</p>
              {manualError && <p className="text-sm text-red-600 mt-2">{manualError}</p>}
            </div>
            <div className="flex justify-end">
              <Button
                className="rounded-full bg-gray-900 text-white hover:bg-gray-800 disabled:opacity-60"
                onClick={addManualRows}
                disabled={manualSubmitting}
              >
                {manualSubmitting ? 'Adding...' : 'Add to staging'}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      <ZoteroCollectionsModal
        open={showZoteroModal}
        onClose={() => {
          setShowZoteroModal(false)
          setSelectedCollections({})
          setZoteroError(null)
        }}
        collections={zoteroCollections}
        selected={selectedCollections}
        setSelected={setSelectedCollections}
        loading={zoteroLoading}
        error={zoteroError}
        onOpenSettings={() => navigate('/settings/integrations?provider=zotero')}
        onConfirm={async () => {
          if (!sessionId) return
          const keys = Object.entries(selectedCollections)
            .filter(([, value]) => value)
            .map(([key]) => key)
          if (!keys.length) {
            setZoteroError('Select at least one collection')
            return
          }
          setZoteroLoading(true)
          setZoteroError(null)
          try {
            for (const key of keys) {
              const res = await apiClient(
                'POST',
                `${endpoints.seedsSession}/${sessionId}/zotero/collections/${key}/stage`,
                { action: 'stage_all' }
              )
              if (res.error) throw new Error(res.error)
            }
            setShowZoteroModal(false)
            setSelectedCollections({})
            fetchRows()
          } catch (err) {
            setZoteroError(err.message || 'Failed to import from Zotero')
          }
          setZoteroLoading(false)
        }}
      />

      <PdfUploadModal
        open={showPdfModal}
        onClose={() => {
          setShowPdfModal(false)
          setPdfFiles([])
          setPdfError(null)
          setGrobidStatus(DEFAULT_GROBID_STATUS)
        }}
        files={pdfFiles}
        setFiles={setPdfFiles}
        loading={pdfLoading}
        error={pdfError}
        grobidStatus={grobidStatus}
        onOpenGrobidGuide={() => navigate('/help/grobid')}
        onConfirm={async () => {
          if (!sessionId || !pdfFiles.length) {
            setPdfError('Select at least one PDF file')
            return
          }
          setPdfLoading(true)
          setPdfError(null)
          try {
            const uploadForm = new FormData()
            pdfFiles.forEach((file) => uploadForm.append('files', file))
            const upload = await apiClient('POST', `${endpoints.seedsSession}/${sessionId}/pdfs/upload`, uploadForm)
            if (upload.error) throw new Error(upload.error)
            const uploadId = upload.data?.upload_id
            if (!uploadId) throw new Error('Upload failed to return upload_id')
            const extract = await apiClient('POST', `${endpoints.seedsSession}/${sessionId}/pdfs/${uploadId}/extract`)
            if (extract.error) throw new Error(extract.error)
            const reviews = (extract.data?.results || []).map((result) => ({
              filename: result.filename,
              action: result.success ? 'accept' : 'skip',
              edited_metadata: result.metadata,
            }))
            const reviewRes = await apiClient(
              'POST',
              `${endpoints.seedsSession}/${sessionId}/pdfs/${uploadId}/review`,
              { reviews }
            )
            if (reviewRes.error) throw new Error(reviewRes.error)
            const stage = await apiClient('POST', `${endpoints.seedsSession}/${sessionId}/pdfs/${uploadId}/stage`)
            if (stage.error) throw new Error(stage.error)
            setShowPdfModal(false)
            setPdfFiles([])
            fetchRows()
          } catch (err) {
            setPdfError(err.message || 'Failed to import PDFs')
          }
          setPdfLoading(false)
        }}
      />
    </div>
  )
}

function normalizeDoi(value) {
  if (!value) return null
  const trimmed = value.trim()
  if (!trimmed) return null
  const normalized = trimmed
    .replace('https://doi.org/', '')
    .replace('http://doi.org/', '')
    .replace(/^doi:/i, '')
    .trim()
  return normalized.startsWith('10.') ? normalized : null
}
