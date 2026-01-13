import { useCallback, useEffect, useMemo, useState } from 'react'
import { AlertCircle, Download, Loader2, RefreshCcw } from 'lucide-react'

import { Button } from '@/components/ui/button'
import apiClient from '@/shared/api/client'
import { endpoints } from '@/shared/api/endpoints'
import config from '@/shared/config/env'
import { useToast } from '@/hooks/use-toast'

import {
  CATALOG_FILTERABLE_COLUMNS,
  CATALOG_ANNOTATION_MARKS,
  CATALOG_ANNOTATION_MARK_VALUES,
} from '../catalogFilters'
import { downloadTextFile, getAnnotationSwatchClass, getPreferredPaperUrl } from '../utils'
import CatalogToolbar from './CatalogToolbar'
import CatalogFilterSidebar from './CatalogFilterSidebar'
import ColumnFilterChips from './ColumnFilterChips'
import CatalogSelectionBar from './CatalogSelectionBar'
import CatalogTable from './CatalogTable'

const ALL_ANNOTATION_MARK_VALUES = CATALOG_ANNOTATION_MARK_VALUES || []

const CATALOG_SORT_COLUMN_MAP = {
  title: 'title',
  authors: 'authors_display',
  year: 'year',
  venue: 'venue',
  identifier: 'doi',
  citation_count: 'citation_count',
  centrality_in: 'centrality_in',
  centrality_out: 'centrality_out',
}

export default function CatalogSection({
  jobId,
  topics = [],
  catalogEnabled,
  catalogLoading,
  catalogError,
  catalogPapers = [],
  catalogTotal,
  catalogPage,
  setCatalogPage,
  catalogPageSize,
  catalogFilters,
  updateCatalogFilter,
  refreshCatalog,
  catalogSort,
  setCatalogSort,
  columnFilters,
  columnOptions,
  columnCustomFilters,
  applyColumnFilter,
  applyColumnCustomFilter,
  clearColumnFilter,
  clearAllColumnFilters,
  fetchCatalogColumnOptions,
  onOpenPaperDetails,
}) {
  const [catalogSearchDraft, setCatalogSearchDraft] = useState(catalogFilters.search || '')
  const [catalogVenueDraft, setCatalogVenueDraft] = useState(catalogFilters.venue || '')
  const [catalogYearFromDraft, setCatalogYearFromDraft] = useState(catalogFilters.yearFrom || '')
  const [catalogYearToDraft, setCatalogYearToDraft] = useState(catalogFilters.yearTo || '')
  const [exportingCatalog, setExportingCatalog] = useState(false)
  const [selectedPaperIds, setSelectedPaperIds] = useState(() => new Set())
  const [markSavingIds, setMarkSavingIds] = useState(() => new Set())
  const [bulkMarkState, setBulkMarkState] = useState({ loading: false, mark: null })
  const [copyingSelection, setCopyingSelection] = useState(false)
  const [downloadingSelection, setDownloadingSelection] = useState(false)
  const { toast } = useToast()

  useEffect(() => {
    setCatalogSearchDraft(catalogFilters.search || '')
  }, [catalogFilters.search])

  useEffect(() => {
    setCatalogVenueDraft(catalogFilters.venue || '')
  }, [catalogFilters.venue])

  useEffect(() => {
    setCatalogYearFromDraft(catalogFilters.yearFrom || '')
  }, [catalogFilters.yearFrom])

  useEffect(() => {
    setCatalogYearToDraft(catalogFilters.yearTo || '')
  }, [catalogFilters.yearTo])

  useEffect(() => {
    setSelectedPaperIds(new Set())
  }, [jobId, catalogEnabled])

  const visiblePaperIds = useMemo(() => {
    if (!Array.isArray(catalogPapers)) return []
    return catalogPapers
      .map((paper) => paper?.paper_id)
      .filter((value) => typeof value === 'string' && value.trim().length > 0)
  }, [catalogPapers])

  const selectionCount = selectedPaperIds.size
  const allVisibleSelected = useMemo(() => {
    if (!visiblePaperIds.length) return false
    return visiblePaperIds.every((id) => selectedPaperIds.has(id))
  }, [visiblePaperIds, selectedPaperIds])
  const someVisibleSelected = useMemo(() => {
    if (!visiblePaperIds.length) return false
    return visiblePaperIds.some((id) => selectedPaperIds.has(id)) && !allVisibleSelected
  }, [visiblePaperIds, selectedPaperIds, allVisibleSelected])

  const availableTopicFilters = useMemo(() => {
    if (!Array.isArray(topics)) return []
    return topics
      .map((topic) => {
        const topicId = topic?.topic_id ?? topic?.id
        if (topicId === undefined || topicId === null) return null
        const label = topic?.topic_label || `Topic ${topicId}`
        return {
          id: String(topicId),
          label,
          paperCount: topic?.paper_count ?? null,
        }
      })
      .filter(Boolean)
  }, [topics])

  const selectedTopicIds = useMemo(
    () =>
      Array.isArray(catalogFilters.topics)
        ? catalogFilters.topics.map((value) => String(value))
        : [],
    [catalogFilters.topics]
  )

  const annotationSelection = useMemo(() => {
    const sourceValues =
      Array.isArray(catalogFilters.marks) && catalogFilters.marks.length
        ? catalogFilters.marks
        : ALL_ANNOTATION_MARK_VALUES
    return new Set(sourceValues)
  }, [catalogFilters.marks])

  const annotationMarksWithSwatch = useMemo(
    () =>
      CATALOG_ANNOTATION_MARKS.map((mark) => ({
        ...mark,
        swatchClass: getAnnotationSwatchClass(mark.value),
      })),
    []
  )

  const activeGeneralFilterCount = useMemo(() => {
    let count = 0
    if ((catalogFilters.venue || '').trim()) count += 1
    if ((catalogFilters.yearFrom || '').trim()) count += 1
    if ((catalogFilters.yearTo || '').trim()) count += 1
    const topicSelections = Array.isArray(catalogFilters.topics)
      ? catalogFilters.topics.filter((value) => `${value}`.trim().length > 0)
      : []
    if (topicSelections.length) count += 1
    const marksArray = Array.isArray(catalogFilters.marks) ? catalogFilters.marks : []
    const marksAreDefault =
      marksArray.length === 0 ||
      marksArray.length === ALL_ANNOTATION_MARK_VALUES.length ||
      ALL_ANNOTATION_MARK_VALUES.every((value) => marksArray.includes(value))
    if (!marksAreDefault) count += 1
    if ((catalogFilters.doiFilter || 'all') !== 'all') count += 1
    if ((catalogFilters.seedFilter || 'all') !== 'all') count += 1
    if ((catalogFilters.retractionFilter || 'all') !== 'all') count += 1
    return count
  }, [catalogFilters])

  const effectivePageSize = catalogPageSize || 25
  const catalogTotalPages = Math.max(1, Math.ceil((catalogTotal || 0) / effectivePageSize))
  const catalogRangeStart = catalogTotal === 0 ? 0 : (catalogPage - 1) * effectivePageSize + 1
  const catalogRangeEnd =
    catalogTotal === 0 ? 0 : Math.min(catalogRangeStart + effectivePageSize - 1, catalogTotal)
  const hasCatalogPapers = catalogPapers.length > 0
  const hasVisiblePapers = visiblePaperIds.length > 0

  const activeColumnFilterChips = useMemo(() => {
    return CATALOG_FILTERABLE_COLUMNS.map(({ key, label }) => {
      const selectionCount = columnFilters[key]?.length || 0
      const hasCustom = Boolean(columnCustomFilters[key])
      if (!selectionCount && !hasCustom) return null
      let descriptor = ''
      if (selectionCount) descriptor = `${selectionCount} selected`
      if (hasCustom) descriptor = descriptor ? `${descriptor} + custom` : 'Custom filter'
      return { key, label, descriptor }
    }).filter(Boolean)
  }, [columnFilters, columnCustomFilters])

  const handleCatalogExport = useCallback(async () => {
    if (!catalogEnabled || !jobId) return
    setExportingCatalog(true)
    try {
      const baseUrl =
        (config?.apiUrl && config.apiUrl.trim()) ||
        (typeof window !== 'undefined' ? window.location.origin : '')
      const relativePath = `${endpoints.crawler}/jobs/${encodeURIComponent(jobId)}/papers/export`
      let exportUrl = relativePath
      if (baseUrl) {
        try {
          exportUrl = new URL(relativePath, baseUrl).toString()
        } catch (_) {
          const sanitizedBase = baseUrl.replace(/\/+$/g, '')
          exportUrl = `${sanitizedBase}${relativePath.startsWith('/') ? '' : '/'}${relativePath}`
        }
      }

      const response = await fetch(exportUrl)
      if (!response.ok) {
        const message = await response.text()
        throw new Error(message || 'Unable to export catalog.')
      }
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const anchor = document.createElement('a')
      anchor.href = url
      anchor.download = `${jobId}_papers.xlsx`
      document.body.appendChild(anchor)
      anchor.click()
      anchor.remove()
      window.URL.revokeObjectURL(url)
    } catch (err) {
      console.error(err)
      toast({
        title: 'Export failed',
        description: err?.message || 'Unable to export catalog.',
        variant: 'destructive',
      })
    } finally {
      setExportingCatalog(false)
    }
  }, [catalogEnabled, jobId, toast])

  const handleCatalogSearchSubmit = (event) => {
    event.preventDefault()
    updateCatalogFilter('search', catalogSearchDraft.trim())
  }

  const handleCatalogSearchReset = () => {
    setCatalogSearchDraft('')
    updateCatalogFilter('search', '')
  }

  const handleCatalogVenueSubmit = (event) => {
    event.preventDefault()
    updateCatalogFilter('venue', catalogVenueDraft.trim())
  }

  const handleCatalogVenueReset = () => {
    setCatalogVenueDraft('')
    updateCatalogFilter('venue', '')
  }

  const handleCatalogYearSubmit = (event) => {
    event.preventDefault()
    updateCatalogFilter('yearFrom', catalogYearFromDraft.trim())
    updateCatalogFilter('yearTo', catalogYearToDraft.trim())
  }

  const handleCatalogYearReset = () => {
    setCatalogYearFromDraft('')
    setCatalogYearToDraft('')
    updateCatalogFilter('yearFrom', '')
    updateCatalogFilter('yearTo', '')
  }

  const handleTopicToggle = (topicId) => {
    const normalized = String(topicId)
    const existing = Array.isArray(catalogFilters.topics)
      ? catalogFilters.topics.map((value) => String(value))
      : []
    const next = existing.includes(normalized)
      ? existing.filter((value) => value !== normalized)
      : [...existing, normalized]
    updateCatalogFilter('topics', next)
  }

  const handleTopicFiltersReset = () => {
    updateCatalogFilter('topics', [])
  }

  const handleTopicSelectAll = () => {
    updateCatalogFilter(
      'topics',
      availableTopicFilters.map((topic) => topic.id)
    )
  }

  const handleSidebarFiltersReset = () => {
    handleCatalogVenueReset()
    handleCatalogYearReset()
    handleTopicFiltersReset()
    handleAnnotationSelectAll()
    updateCatalogFilter('doiFilter', 'all')
    updateCatalogFilter('seedFilter', 'all')
    updateCatalogFilter('retractionFilter', 'all')
  }

  const handlePresenceFilterChange = (filterKey, value) => {
    updateCatalogFilter(filterKey, value)
  }

  const handleAnnotationToggle = (markValue) => {
    const baseValues =
      Array.isArray(catalogFilters.marks) && catalogFilters.marks.length
        ? catalogFilters.marks
        : ALL_ANNOTATION_MARK_VALUES
    const nextSet = new Set(baseValues)
    if (nextSet.has(markValue)) {
      if (nextSet.size === 1) return
      nextSet.delete(markValue)
    } else {
      nextSet.add(markValue)
    }
    updateCatalogFilter('marks', Array.from(nextSet))
  }

  const handleAnnotationSelectAll = () => {
    updateCatalogFilter('marks', [...ALL_ANNOTATION_MARK_VALUES])
  }

  const handleCopySelectedUrls = useCallback(async () => {
    if (!selectedPaperIds.size) {
      toast({
        title: 'No papers selected',
        description: 'Select at least one paper in the table first.',
        variant: 'destructive',
      })
      return
    }
    const selectedPapers = catalogPapers.filter((paper) =>
      paper?.paper_id ? selectedPaperIds.has(paper.paper_id) : false
    )
    const urls = selectedPapers
      .map((paper) => getPreferredPaperUrl(paper))
      .filter((value) => typeof value === 'string' && value.length > 0)
    if (!urls.length) {
      toast({
        title: 'No URLs to copy',
        description: 'Selected papers do not have DOI or source URLs.',
        variant: 'destructive',
      })
      return
    }
    setCopyingSelection(true)
    try {
      await navigator.clipboard.writeText(urls.join('\n'))
      toast({
        title: `Copied ${urls.length} link${urls.length === 1 ? '' : 's'}`,
        description: 'Ready to paste into NotebookLM or other tools.',
        variant: 'success',
      })
    } catch (err) {
      toast({
        title: 'Unable to copy links',
        description: err?.message || 'Clipboard permission was denied.',
        variant: 'destructive',
      })
    } finally {
      setCopyingSelection(false)
    }
  }, [catalogPapers, selectedPaperIds, toast])

  const handleDownloadSelectedUrls = useCallback(() => {
    if (!selectedPaperIds.size) {
      toast({
        title: 'No papers selected',
        description: 'Select at least one paper in the table first.',
        variant: 'destructive',
      })
      return
    }
    const selectedPapers = catalogPapers.filter((paper) =>
      paper?.paper_id ? selectedPaperIds.has(paper.paper_id) : false
    )
    const urls = selectedPapers
      .map((paper) => getPreferredPaperUrl(paper))
      .filter((value) => typeof value === 'string' && value.length > 0)
    if (!urls.length) {
      toast({
        title: 'No URLs to download',
        description: 'Selected papers do not have DOI or source URLs.',
        variant: 'destructive',
      })
      return
    }
    setDownloadingSelection(true)
    try {
      downloadTextFile('selected_papers.txt', urls.join('\n'))
      toast({
        title: `Downloaded ${urls.length} link${urls.length === 1 ? '' : 's'}`,
        description: 'Check your downloads folder for selected_papers.txt.',
      })
    } catch (err) {
      toast({
        title: 'Unable to download links',
        description: err?.message || 'Something went wrong while creating the file.',
        variant: 'destructive',
      })
    } finally {
      setDownloadingSelection(false)
    }
  }, [catalogPapers, selectedPaperIds, toast])

  const handleCatalogPageChange = (direction) => {
    setCatalogPage((prev) => {
      const candidate = prev + direction
      if (candidate < 1) return 1
      if (candidate > catalogTotalPages) return catalogTotalPages
      return candidate
    })
  }

  const togglePaperSelection = (paperId) => {
    if (!paperId) return
    setSelectedPaperIds((prev) => {
      const next = new Set(prev)
      if (next.has(paperId)) {
        next.delete(paperId)
      } else {
        next.add(paperId)
      }
      return next
    })
  }

  const toggleSelectVisibleRows = () => {
    if (!visiblePaperIds.length) return
    setSelectedPaperIds((prev) => {
      const next = new Set(prev)
      if (allVisibleSelected) {
        visiblePaperIds.forEach((id) => next.delete(id))
      } else {
        visiblePaperIds.forEach((id) => next.add(id))
      }
      return next
    })
  }

  const clearSelection = () => setSelectedPaperIds(new Set())

  const markPapers = useCallback(
    async (paperIds, markValue, { skipBulkState = false } = {}) => {
      if (!jobId || !Array.isArray(paperIds) || !paperIds.length) return false
      const ids = paperIds.filter((value) => typeof value === 'string' && value)
      if (!ids.length) return false
      if (!skipBulkState) {
        setBulkMarkState({ loading: true, mark: markValue })
      }
      const failures = []
      for (const id of ids) {
        setMarkSavingIds((prev) => {
          const next = new Set(prev)
          next.add(id)
          return next
        })
        const res = await apiClient(
          'POST',
          `${endpoints.crawler}/jobs/${jobId}/papers/${encodeURIComponent(id)}/mark`,
          { mark: markValue }
        )
        if (res.error) {
          failures.push(res.error)
        }
        setMarkSavingIds((prev) => {
          const next = new Set(prev)
          next.delete(id)
          return next
        })
      }
      if (!skipBulkState) {
        setBulkMarkState({ loading: false, mark: null })
      }
      if (failures.length) {
        toast({
          title: 'Unable to update annotations',
          description: failures[0] || 'Something went wrong while updating marks.',
          variant: 'destructive',
        })
        return false
      }
      toast({
        title: 'Annotations updated',
        description:
          markValue === 'standard'
            ? `Cleared annotations for ${ids.length} paper${ids.length === 1 ? '' : 's'}.`
            : `Marked ${ids.length} paper${ids.length === 1 ? '' : 's'} as ${markValue}.`,
        variant: 'success',
      })
      refreshCatalog()
      return true
    },
    [jobId, refreshCatalog, toast]
  )

  const handleInlineMarkChange = (paperId, markValue) => {
    if (!paperId) return
    markPapers([paperId], markValue, { skipBulkState: true })
  }

  const handleBulkMark = async (markValue) => {
    const ids = Array.from(selectedPaperIds)
    if (!ids.length) return
    const success = await markPapers(ids, markValue, { skipBulkState: false })
    if (success) {
      setSelectedPaperIds(new Set())
    }
  }

  const handleCatalogSortToggle = (columnKey) => {
    const backendKey = CATALOG_SORT_COLUMN_MAP[columnKey]
    if (!backendKey) return
    setCatalogSort((prev) => {
      if (!prev || prev.key !== backendKey) {
        return { key: backendKey, direction: 'desc' }
      }
      return {
        key: backendKey,
        direction: prev.direction === 'asc' ? 'desc' : 'asc',
      }
    })
  }

  return (
    <section className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-2xl font-semibold text-gray-900">All papers</h2>
          <p className="text-sm text-gray-500">
            Browse every paper captured by this crawl and search across the catalog.
          </p>
        </div>
        <div className="flex gap-2 flex-wrap">
          <Button
            variant="outline"
            className="rounded-full"
            onClick={handleCatalogExport}
            disabled={exportingCatalog || !catalogEnabled}
          >
            {exportingCatalog ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin mr-2" />
                Preparing…
              </>
            ) : (
              <>
                <Download className="w-4 h-4 mr-2" />
                Export (.xlsx)
              </>
            )}
          </Button>
          <Button
            variant="outline"
            className="rounded-full"
            onClick={refreshCatalog}
            disabled={catalogLoading || !catalogEnabled}
          >
            {catalogLoading ? (
              <Loader2 className="w-4 h-4 animate-spin mr-2" />
            ) : (
              <RefreshCcw className="w-4 h-4 mr-2" />
            )}
            Refresh
          </Button>
        </div>
      </div>
      <div className="flex flex-col gap-6 lg:flex-row">
        <CatalogFilterSidebar
          catalogEnabled={catalogEnabled}
          activeGeneralFilterCount={activeGeneralFilterCount}
          catalogSearchDraft={catalogSearchDraft}
          onCatalogSearchChange={setCatalogSearchDraft}
          onCatalogSearchSubmit={handleCatalogSearchSubmit}
          onCatalogSearchReset={handleCatalogSearchReset}
          catalogVenueDraft={catalogVenueDraft}
          onCatalogVenueChange={setCatalogVenueDraft}
          onCatalogVenueSubmit={handleCatalogVenueSubmit}
          onCatalogVenueReset={handleCatalogVenueReset}
          catalogYearFromDraft={catalogYearFromDraft}
          catalogYearToDraft={catalogYearToDraft}
          onCatalogYearFromChange={setCatalogYearFromDraft}
          onCatalogYearToChange={setCatalogYearToDraft}
          onCatalogYearSubmit={handleCatalogYearSubmit}
          onCatalogYearReset={handleCatalogYearReset}
          availableTopicFilters={availableTopicFilters}
          selectedTopicIds={selectedTopicIds}
          onTopicToggle={handleTopicToggle}
          onTopicSelectAll={handleTopicSelectAll}
          onTopicFiltersReset={handleTopicFiltersReset}
          annotationMarks={annotationMarksWithSwatch}
          annotationSelection={annotationSelection}
          onAnnotationToggle={handleAnnotationToggle}
          onAnnotationSelectAll={handleAnnotationSelectAll}
          catalogFilters={catalogFilters}
          onPresenceFilterChange={handlePresenceFilterChange}
          onSidebarReset={handleSidebarFiltersReset}
        />
        <div className="flex-1 min-w-0 space-y-4">
          {catalogError ? (
            <div className="rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-red-700 flex gap-2 items-start">
              <AlertCircle className="w-4 h-4 mt-0.5" />
              <div>{catalogError}</div>
            </div>
          ) : null}
          {catalogLoading ? (
            <div className="rounded-3xl border border-dashed border-gray-300 p-6 text-center text-gray-600">
              <Loader2 className="w-4 h-4 animate-spin inline-block mr-2" />
              Loading catalog…
            </div>
          ) : hasCatalogPapers ? (
            <>
              <ColumnFilterChips
                chips={activeColumnFilterChips}
                onClearChip={clearColumnFilter}
                onClearAll={clearAllColumnFilters}
              />
              <CatalogSelectionBar
                selectionCount={selectionCount}
                onClearSelection={clearSelection}
                annotationMarks={CATALOG_ANNOTATION_MARKS}
                onBulkMark={handleBulkMark}
                bulkMarkState={bulkMarkState}
                onCopySelected={handleCopySelectedUrls}
                copyingSelections={copyingSelection}
                onDownloadSelected={handleDownloadSelectedUrls}
                downloadingSelections={downloadingSelection}
              />
              <CatalogTable
                catalogPapers={catalogPapers}
                columnFilters={columnFilters}
                columnCustomFilters={columnCustomFilters}
                columnOptions={columnOptions}
                applyColumnFilter={applyColumnFilter}
                applyColumnCustomFilter={applyColumnCustomFilter}
                fetchCatalogColumnOptions={fetchCatalogColumnOptions}
                catalogSort={catalogSort}
                onSortToggle={handleCatalogSortToggle}
                catalogEnabled={catalogEnabled}
                catalogLoading={catalogLoading}
                annotationMarks={CATALOG_ANNOTATION_MARKS}
                selectedPaperIds={selectedPaperIds}
                onTogglePaperSelection={togglePaperSelection}
                onToggleVisibleRows={toggleSelectVisibleRows}
                allVisibleSelected={allVisibleSelected}
                hasVisiblePapers={hasVisiblePapers}
                someVisibleSelected={someVisibleSelected}
                markSavingIds={markSavingIds}
                bulkMarkState={bulkMarkState}
                onInlineMarkChange={handleInlineMarkChange}
                onOpenPaperDetails={onOpenPaperDetails}
              />
              <div className="flex flex-wrap items-center justify-between gap-3 pt-2 text-sm text-gray-600">
                <span>
                  Showing {catalogRangeStart}-{catalogRangeEnd} of {catalogTotal} papers
                </span>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    className="rounded-full"
                    onClick={() => handleCatalogPageChange(-1)}
                    disabled={catalogLoading || catalogPage === 1}
                  >
                    Previous
                  </Button>
                  <Button
                    variant="outline"
                    className="rounded-full"
                    onClick={() => handleCatalogPageChange(1)}
                    disabled={catalogLoading || catalogPage >= catalogTotalPages}
                  >
                    Next
                  </Button>
                </div>
              </div>
            </>
          ) : (
            <p className="text-sm text-gray-500">No papers to display yet.</p>
          )}
        </div>
      </div>
    </section>
  )
}
