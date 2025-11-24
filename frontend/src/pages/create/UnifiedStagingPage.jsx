import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import { useNavigate } from 'react-router-dom'
import { AlertCircle, Check, ChevronDown, Filter, Loader2, RefreshCw, X } from 'lucide-react'
import Stepper from '@/components/Stepper'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import apiClient from '@/shared/api/client'
import { endpoints } from '@/shared/api/endpoints'
import { getSessionId, hydrateSessionFromQuery } from '@/shared/lib/session'

const workflowSteps = ['Add', 'Stage', 'Match', 'Library']
const editableFields = ['title', 'authors', 'year', 'venue', 'doi', 'url', 'abstract']
const defaultGrobidStatus = { checked: false, available: true, message: null }
const FILTERABLE_COLUMNS = [
  { key: 'title', label: 'Title' },
  { key: 'authors', label: 'Authors' },
  { key: 'year', label: 'Year' },
  { key: 'venue', label: 'Venue' },
  { key: 'identifier', label: 'Identifiers' },
]
const COLUMN_QUERY_MAP = {
  title: 'title_values',
  authors: 'author_values',
  year: 'year_values',
  venue: 'venue_values',
  identifier: 'identifier_values',
}
const createColumnState = () =>
  FILTERABLE_COLUMNS.reduce((acc, { key }) => {
    acc[key] = []
    return acc
  }, {})
const createColumnCustomState = () =>
  FILTERABLE_COLUMNS.reduce((acc, { key }) => {
    acc[key] = null
    return acc
  }, {})
const TEXT_FILTER_OPERATIONS = [
  { value: 'equals', label: 'Equals' },
  { value: 'not_equals', label: 'Does not equal' },
  { value: 'begins_with', label: 'Begins with' },
  { value: 'not_begins_with', label: 'Does not begin with' },
  { value: 'ends_with', label: 'Ends with' },
  { value: 'not_ends_with', label: 'Does not end with' },
  { value: 'contains', label: 'Contains' },
  { value: 'not_contains', label: 'Does not contain' },
]
const NUMBER_FILTER_OPERATIONS = [
  { value: 'equals', label: 'Equals' },
  { value: 'not_equals', label: 'Does not equal' },
  { value: 'greater_than', label: 'Is greater than' },
  { value: 'greater_than_or_equal', label: 'Is greater than or equal to' },
  { value: 'less_than', label: 'Is less than' },
  { value: 'less_than_or_equal', label: 'Is less than or equal to' },
  { value: 'between', label: 'Is between' },
  { value: 'not_between', label: 'Is not between' },
]
const FILTER_OPERATION_DESCRIPTIONS = TEXT_FILTER_OPERATIONS.concat(NUMBER_FILTER_OPERATIONS).reduce(
  (acc, item) => {
    acc[item.value] = item.label
    return acc
  },
  {}
)
const getColumnType = (columnKey) => (columnKey === 'year' ? 'number' : 'text')

export default function UnifiedStagingPage() {
  const navigate = useNavigate()
  const [sessionId, setSessionId] = useState(null)
  const [rows, setRows] = useState([])
  const [loading, setLoading] = useState(true)
  const [fetchError, setFetchError] = useState(null)
  const [page, setPage] = useState(1)
  const [pageSize] = useState(25)
  const [totalPages, setTotalPages] = useState(1)
  const [stats, setStats] = useState({ totalRows: 0, filteredRows: 0, selectedCount: 0 })
  const [filters, setFilters] = useState({
    sources: [],
    yearMin: '',
    yearMax: '',
    title: '',
    venue: '',
    author: '',
    keyword: '',
    doi: 'all',
    selectedOnly: false,
  })
  const [sort, setSort] = useState({ field: null, direction: 'asc' })
  const [showAddMenu, setShowAddMenu] = useState(false)
  const [sourceOptions, setSourceOptions] = useState([])
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
  const [grobidStatus, setGrobidStatus] = useState(defaultGrobidStatus)
  const [editing, setEditing] = useState({ id: null, field: null, value: '' })
  const [matching, setMatching] = useState(false)
  const [columnFilters, setColumnFilters] = useState(() => createColumnState())
  const [columnCustomFilters, setColumnCustomFilters] = useState(() => createColumnCustomState())
  const [columnOptions, setColumnOptions] = useState(() => createColumnState())
  const columnFilterValues = useMemo(
    () =>
      FILTERABLE_COLUMNS.reduce((acc, { key }) => {
        acc[key] = columnFilters[key].map((item) => item.value)
        return acc
      }, {}),
    [columnFilters]
  )
  const activeColumnFilterCount = useMemo(
    () =>
      FILTERABLE_COLUMNS.reduce(
        (total, { key }) =>
          total + (columnFilters[key]?.length || 0) + (columnCustomFilters[key] ? 1 : 0),
        0
      ),
    [columnFilters, columnCustomFilters]
  )

  useEffect(() => {
    const sid = getSessionId() || hydrateSessionFromQuery()
    if (!sid) {
      navigate('/')
      return
    }
    setSessionId(sid)
  }, [navigate])

  const fetchRows = useCallback(async () => {
    if (!sessionId) return
    setLoading(true)
    setFetchError(null)
    const query = {
      page,
      page_size: pageSize,
      sort_by: sort.field || undefined,
      sort_dir: sort.direction,
      selected_only: filters.selectedOnly ? 'true' : undefined,
      title: filters.title || undefined,
      venue: filters.venue || undefined,
      author: filters.author || undefined,
      keyword: filters.keyword || undefined,
      doi_presence:
        filters.doi === 'with' ? 'with' : filters.doi === 'without' ? 'without' : undefined,
      year_min: filters.yearMin || undefined,
      year_max: filters.yearMax || undefined,
    }
    if (filters.sources.length) query.sources = filters.sources
    FILTERABLE_COLUMNS.forEach(({ key }) => {
      const values = columnFilterValues[key]
      if (values && values.length) {
        query[COLUMN_QUERY_MAP[key]] = values
      }
    })
    const customFiltersPayload = []
    FILTERABLE_COLUMNS.forEach(({ key }) => {
      const custom = columnCustomFilters[key]
      if (!custom || !custom.operator) return
      const primaryValue = `${custom.value ?? ''}`.trim()
      if (!primaryValue) return
      let payload = `${key}::${custom.operator}::${primaryValue}`
      if (custom.valueTo !== undefined && custom.valueTo !== null) {
        const secondaryValue = `${custom.valueTo}`.trim()
        if (secondaryValue) {
          payload = `${payload}::${secondaryValue}`
        }
      }
      customFiltersPayload.push(payload)
    })
    if (customFiltersPayload.length) {
      query.column_filters = customFiltersPayload
    }
    const res = await apiClient('GET', `${endpoints.seedsSession}/${sessionId}/staging`, null, { query })
    if (res.error) {
      setFetchError(res.error)
    } else {
      const data = res.data || {}
      setRows(data.rows || [])
      setStats({
        totalRows: data.total_rows || 0,
        filteredRows: data.filtered_rows || data.total_rows || 0,
        selectedCount: data.selected_count || 0,
      })
      const nextOptions = createColumnState()
      const optionPayload = data.column_options || {}
      FILTERABLE_COLUMNS.forEach(({ key }) => {
        const columnOption = optionPayload[key]
        nextOptions[key] = Array.isArray(columnOption) ? columnOption : []
      })
      setColumnOptions(nextOptions)
      setTotalPages(data.total_pages || 1)
      if (page > (data.total_pages || 1)) setPage(1)
      const newOptions = (data.rows || []).reduce((acc, row) => {
        if (row.source) acc.add(row.source)
        return acc
      }, new Set(filters.sources))
      setSourceOptions((prev) => {
        const combined = new Set(prev)
        newOptions.forEach((value) => combined.add(value))
        return Array.from(combined).filter(Boolean).sort()
      })
    }
    setLoading(false)
  }, [
    sessionId,
    page,
    pageSize,
    sort.field,
    sort.direction,
    filters.selectedOnly,
    filters.title,
    filters.venue,
    filters.author,
    filters.keyword,
    filters.doi,
    filters.yearMin,
    filters.yearMax,
    filters.sources,
    columnFilterValues,
    columnCustomFilters,
  ])

  useEffect(() => {
    fetchRows()
  }, [fetchRows])

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
    setGrobidStatus(defaultGrobidStatus)
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

  const availableSources = useMemo(() => {
    const set = new Set(sourceOptions)
    filters.sources.forEach((value) => set.add(value))
    return Array.from(set).filter(Boolean).sort()
  }, [sourceOptions, filters.sources])

  const resetFilters = () => {
    setFilters({
      sources: [],
      yearMin: '',
      yearMax: '',
      title: '',
      venue: '',
      author: '',
      keyword: '',
      doi: 'all',
      selectedOnly: false,
    })
    setColumnFilters(createColumnState())
    setColumnCustomFilters(createColumnCustomState())
    setPage(1)
  }

  const handleColumnFilterApply = (columnKey, selections) => {
    const safeSelections = Array.isArray(selections) ? selections : []
    setColumnFilters((prev) => {
      const next = { ...prev }
      const deduped = []
      const seen = new Set()
      safeSelections.forEach((item) => {
        if (!item || !item.value || seen.has(item.value)) return
        seen.add(item.value)
        deduped.push({
          value: item.value,
          label: item.label || item.value,
          meta: item.meta || null,
        })
      })
      next[columnKey] = deduped
      return next
    })
    setPage(1)
  }

  const handleColumnCustomFilterApply = (columnKey, customPayload) => {
    setColumnCustomFilters((prev) => ({ ...prev, [columnKey]: customPayload }))
    setPage(1)
  }

  const clearColumnFilter = (columnKey) => {
    setColumnFilters((prev) => ({ ...prev, [columnKey]: [] }))
    setColumnCustomFilters((prev) => ({ ...prev, [columnKey]: null }))
    setPage(1)
  }

  const clearAllColumnFilters = () => {
    setColumnFilters(createColumnState())
    setColumnCustomFilters(createColumnCustomState())
    setPage(1)
  }

  const toggleSourceFilter = (value) => {
    setFilters((prev) => {
      const exists = prev.sources.includes(value)
      const next = exists ? prev.sources.filter((s) => s !== value) : [...prev.sources, value]
      setPage(1)
      return { ...prev, sources: next }
    })
  }

  const startEditing = (rowId, field, value) => {
    if (!editableFields.includes(field)) return
    setEditing({ id: rowId, field, value: value ?? '' })
  }

  const cancelEditing = () => setEditing({ id: null, field: null, value: '' })

  const commitEditing = async () => {
    if (!editing.id || !editing.field) return
    const value = editing.value
    const payload = {}
    if (editing.field === 'year') {
      payload.year = value ? Number(value) : null
    } else {
      payload[editing.field] = value || null
    }
    await apiClient('PATCH', `${endpoints.seedsSession}/${sessionId}/staging/${editing.id}`, payload)
    cancelEditing()
    fetchRows()
  }

  const handleSelectRow = async (rowId, checked) => {
    await apiClient('POST', `${endpoints.seedsSession}/${sessionId}/staging/select`, {
      staging_ids: [rowId],
      is_selected: checked,
    })
    fetchRows()
  }

  const handleSelectVisible = async (checked) => {
    if (!rows.length) return
    await apiClient('POST', `${endpoints.seedsSession}/${sessionId}/staging/select`, {
      staging_ids: rows.map((row) => row.staging_id),
      is_selected: checked,
    })
    fetchRows()
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

  const toggleSort = (field) => {
    setSort((prev) => {
      if (prev.field === field) {
        const nextDir = prev.direction === 'asc' ? 'desc' : 'asc'
        return { field, direction: nextDir }
      }
      return { field, direction: 'asc' }
    })
  }

  const totalFilteredRows = stats.filteredRows || stats.totalRows || 0
  const hasRows = rows.length > 0
  const rangeStart = hasRows ? (page - 1) * pageSize + 1 : 0
  const rangeEnd = hasRows ? Math.min(rangeStart + rows.length - 1, totalFilteredRows) : 0
  const showInitialEmptyState = !loading && !fetchError && stats.totalRows === 0

  const renderEditableValue = (row, field, placeholder, isTextArea = false) => {
    const isEditing = editing.id === row.staging_id && editing.field === field
    const displayValue = row[field]
    if (isEditing) {
      const inputClass =
        field === 'year'
          ? 'w-24 text-center rounded-full border border-gray-300 px-3 py-2 text-sm shadow-md focus:outline-none focus:ring-2 focus:ring-gray-900'
          : 'w-64 max-w-full rounded-full border border-gray-300 px-3 py-2 text-sm shadow-md focus:outline-none focus:ring-2 focus:ring-gray-900'
      const commonProps = {
        autoFocus: true,
        value: editing.value,
        onChange: (e) => setEditing((prev) => ({ ...prev, value: e.target.value })),
        onBlur: commitEditing,
        onKeyDown: (e) => {
          if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault()
            commitEditing()
          } else if (e.key === 'Escape') {
            cancelEditing()
          }
        },
      }
      if (isTextArea) {
        return (
          <textarea
            rows={4}
            className="w-full min-w-[320px] rounded-3xl border border-gray-200 px-4 py-3 text-sm shadow-md focus:outline-none focus:ring-2 focus:ring-gray-900"
            {...commonProps}
          />
        )
      }
      return <input type={field === 'year' ? 'number' : 'text'} className={inputClass} {...commonProps} />
    }
    return (
      <div
        onDoubleClick={() => startEditing(row.staging_id, field, displayValue ?? '')}
        className="cursor-text"
      >
        {displayValue ? (
          <span className="text-sm text-gray-900">{displayValue}</span>
        ) : (
          <span className="text-sm text-gray-400">{placeholder}</span>
        )}
      </div>
    )
  }

  const renderAddMoreSourcesButton = () => (
    <div className="relative">
      <Button
        variant="outline"
        className="rounded-full border-gray-300 text-gray-900"
        onClick={() => setShowAddMenu((prev) => !prev)}
      >
        Add more sources
        <ChevronDown className="w-4 h-4 ml-2" />
      </Button>
      {showAddMenu && (
        <div className="absolute right-0 mt-2 w-56 rounded-2xl border border-gray-200 bg-white shadow-lg z-20">
          <button
            type="button"
            className="w-full text-left px-4 py-3 text-sm hover:bg-gray-50"
            onClick={() => {
              setManualModalOpen(true)
              setManualError(null)
              setShowAddMenu(false)
            }}
          >
            Manual IDs
            <p className="text-xs text-gray-500">Paste OpenAlex IDs (one per line)</p>
          </button>
          <button
            type="button"
            className="w-full text-left px-4 py-3 text-sm hover:bg-gray-50"
            onClick={handleOpenZoteroPicker}
          >
            Zotero collections
            <p className="text-xs text-gray-500">Pick items from your Zotero library</p>
          </button>
          <button
            type="button"
            className="w-full text-left px-4 py-3 text-sm hover:bg-gray-50 rounded-b-2xl"
            onClick={() => {
              setShowAddMenu(false)
              setShowPdfModal(true)
            }}
          >
            Dump files
            <p className="text-xs text-gray-500">Upload one or more PDF files</p>
          </button>
        </div>
      )}
    </div>
  )

  return (
    <div className="min-h-screen bg-white flex flex-col">
      <div className="pt-8">
        <Stepper currentStep={2} steps={workflowSteps} />
      </div>

      <div className="px-6 pb-10 flex-1 flex flex-col">
        {!showInitialEmptyState && (
          <header className="flex flex-wrap items-center justify-between gap-4 border border-gray-200 rounded-3xl px-6 py-4 bg-white shadow-md
">
          <div>
            <p className="text-sm uppercase tracking-[0.3em] text-gray-500 mb-1">Unified staging</p>
            <h1 className="text-2xl font-semibold text-gray-900">Review, edit, and select seed papers from various sources in one workspace</h1>
          </div>
          <div className="flex items-center gap-2">
            <div className="text-sm text-gray-600">
              <span className="font-semibold text-gray-900">{stats.totalRows}</span> staged •{' '}
              <span className="font-semibold text-gray-900">{stats.selectedCount}</span> selected
            </div>
            {renderAddMoreSourcesButton()}
            <Button
              className="rounded-full bg-gray-900 text-white hover:bg-gray-800 disabled:opacity-60"
              disabled={!stats.selectedCount || matching}
              onClick={runMatching}
            >
              {matching ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
              Next
            </Button>
          </div>
          </header>
        )}

        {showInitialEmptyState ? (
          <div className="flex-1 flex flex-col items-center justify-center text-center px-6 mt-10">
            <div className="max-w-2xl space-y-4">
              <div>
                <p className="text-sm uppercase tracking-[0.3em] text-gray-500 mb-2">No papers staged yet</p>
                <p className="text-2xl font-semibold text-gray-900 mb-3">
                  Bring in papers to get started
                </p>
                <p className="text-base text-gray-600">
                  Pick one of the options below to import papers from manual IDs, Zotero, or dump files.
                </p>
              </div>
              <div className="flex flex-col sm:flex-row gap-3 w-full">
                <Button
                  variant="outline"
                  className="rounded-full flex-1"
                  onClick={() => setManualModalOpen(true)}
                >
                  Manual IDs
                </Button>
                <Button
                  variant="outline"
                  className="rounded-full flex-1"
                  onClick={() => setShowZoteroModal(true)}
                >
                  Zotero collections
                </Button>
                <Button
                  variant="outline"
                  className="rounded-full flex-1"
                  onClick={() => setShowPdfModal(true)}
                >
                  Dump files
                </Button>
              </div>
            </div>
          </div>
        ) : (
          <div className="mt-6 flex-1 flex overflow-hidden">
          {/* Filters */}
          <aside className="w-full max-w-xs border border-gray-200 rounded-3xl p-5 mr-6 bg-white shadow-md
 overflow-y-auto h-fit">
            <div className="flex items-center gap-2 mb-4">
              <Filter className="w-4 h-4 text-gray-500" />
              <span className="text-sm font-semibold text-gray-700">Filters</span>
            </div>
            <div className="space-y-4">
              <div>
                <Label className="text-xs uppercase tracking-wider text-gray-500 mb-2 block">Source</Label>
                <div className="space-y-2 rounded-2xl border border-gray-100 p-3 shadow-md">
                  {availableSources.length === 0 && (
                    <p className="text-xs text-gray-400">Sources appear once you add papers.</p>
                  )}
                  {availableSources.map((source) => (
                    <label key={source} className="flex items-center gap-2 text-sm text-gray-700">
                      <input
                        type="checkbox"
                        className="rounded border-gray-300 text-gray-900 focus:ring-gray-900"
                        checked={filters.sources.includes(source)}
                        onChange={() => toggleSourceFilter(source)}
                      />
                      {source}
                    </label>
                  ))}
                </div>
              </div>

              <div>
                <Label className="text-xs uppercase tracking-wider text-gray-500 mb-1 block">Year range</Label>
                <div className="flex items-center gap-2">
                  <Input
                    type="number"
                    placeholder="From"
                    value={filters.yearMin}
                    className="rounded-full shadow-sm"
                    onChange={(e) => {
                      setFilters((prev) => ({ ...prev, yearMin: e.target.value }))
                      setPage(1)
                    }}
                  />
                  <span className="text-sm text-gray-400">—</span>
                  <Input
                    type="number"
                    placeholder="To"
                    value={filters.yearMax}
                    className="rounded-full shadow-sm"
                    onChange={(e) => {
                      setFilters((prev) => ({ ...prev, yearMax: e.target.value }))
                      setPage(1)
                    }}
                  />
                </div>
              </div>

              <div>
                <Label className="text-xs uppercase tracking-wider text-gray-500 mb-1 block">Title search</Label>
                <Input
                  placeholder="e.g. Transformer"
                  value={filters.title}
                  className="rounded-full shadow-sm"
                  onChange={(e) => {
                    setFilters((prev) => ({ ...prev, title: e.target.value }))
                    setPage(1)
                  }}
                />
              </div>

              <div>
                <Label className="text-xs uppercase tracking-wider text-gray-500 mb-1 block">Author search</Label>
                <Input
                  placeholder="Author name"
                  value={filters.author}
                  className="rounded-full shadow-sm"
                  onChange={(e) => {
                    setFilters((prev) => ({ ...prev, author: e.target.value }))
                    setPage(1)
                  }}
                />
              </div>

              <div>
                <Label className="text-xs uppercase tracking-wider text-gray-500 mb-1 block">Venue search</Label>
                <Input
                  placeholder="Journal, conference..."
                  value={filters.venue}
                  className="rounded-full shadow-sm"
                  onChange={(e) => {
                    setFilters((prev) => ({ ...prev, venue: e.target.value }))
                    setPage(1)
                  }}
                />
              </div>

              <div>
                <Label className="text-xs uppercase tracking-wider text-gray-500 mb-1 block">Keyword / tag</Label>
                <Input
                  placeholder="Search title or abstract"
                  value={filters.keyword}
                  className="rounded-full shadow-sm"
                  onChange={(e) => {
                    setFilters((prev) => ({ ...prev, keyword: e.target.value }))
                    setPage(1)
                  }}
                />
              </div>

              <div>
                <Label className="text-xs uppercase tracking-wider text-gray-500 mb-1 block">DOI filter</Label>
                <div className="flex items-center gap-2">
                  {[
                    { label: 'All', value: 'all' },
                    { label: 'With DOI', value: 'with' },
                    { label: 'No DOI', value: 'without' },
                  ].map((opt) => (
                    <button
                      type="button"
                      key={opt.value}
                      className={`px-4 py-1.5 rounded-full text-xs font-medium border shadow-md ${
                        filters.doi === opt.value
                          ? 'bg-gray-900 text-white border-gray-900'
                          : 'bg-white text-gray-600 border-gray-200 hover:border-gray-400'
                      }`}
                      onClick={() => {
                        setFilters((prev) => ({ ...prev, doi: opt.value }))
                        setPage(1)
                      }}
                    >
                      {opt.label}
                    </button>
                  ))}
                </div>
              </div>

              <label className="flex items-center gap-2 text-sm text-gray-700">
                <input
                  type="checkbox"
                  className="rounded border-gray-300 text-gray-900 focus:ring-gray-900"
                  checked={filters.selectedOnly}
                  onChange={(e) => {
                    setFilters((prev) => ({ ...prev, selectedOnly: e.target.checked }))
                    setPage(1)
                  }}
                />
                Show selected only
              </label>

              <Button variant="ghost" className="w-full rounded-full bg-gray-100 shadow-sm" onClick={resetFilters}>
                Clear filters
              </Button>
            </div>
          </aside>

          {/* Table */}
          <section className="flex-1 flex flex-col border border-gray-200 rounded-3xl bg-white shadow-md overflow-hidden">
            <div className="flex items-center justify-between px-6 py-3 border-b border-gray-100">
              <div className="text-sm text-gray-500">
                {stats.totalRows
                  ? `Showing ${
                      rangeStart && rangeEnd ? `${rangeStart}–${rangeEnd}` : '0'
                    } of ${totalFilteredRows} papers (${stats.totalRows} staged total)`
                  : 'No staged papers yet'}
              </div>
            <div className="flex items-center gap-2 text-sm text-gray-600">
              <button
                type="button"
                className="inline-flex items-center gap-1 text-xs text-gray-500 hover:text-gray-900"
                onClick={() => fetchRows()}
              >
                <RefreshCw className="w-3 h-3" /> Refresh
              </button>
              <button
                type="button"
                className="inline-flex items-center gap-1 text-xs text-gray-500 hover:text-gray-900"
                onClick={() => handleSelectVisible(true)}
              >
                <Check className="w-3 h-3" /> Select visible
              </button>
              <button
                type="button"
                className="inline-flex items-center gap-1 text-xs text-gray-500 hover:text-gray-900"
                onClick={() => handleSelectVisible(false)}
              >
                <span className="text-base leading-none">×</span> Clear visible
              </button>
              <button
                type="button"
                className={`inline-flex items-center gap-1 text-xs ${sort.field === 'selected' ? 'text-gray-900 font-semibold' : 'text-gray-500 hover:text-gray-900'}`}
                onClick={() => {
                  setSort((prev) =>
                    prev.field === 'selected'
                      ? { field: null, direction: 'asc' }
                      : { field: 'selected', direction: 'desc' }
                  )
                }}
              >
                {sort.field === 'selected' ? 'Selected first ✓' : 'Selected first'}
              </button>
            </div>
          </div>
            {activeColumnFilterCount > 0 && (
              <div className="border-b border-gray-100 px-6 py-3 bg-gray-50 flex flex-wrap items-center gap-2">
                {FILTERABLE_COLUMNS.map(({ key, label }) => {
                  const count = columnFilters[key]?.length || 0
                  const hasCustom = Boolean(columnCustomFilters[key])
                  if (!count && !hasCustom) return null
                  const summary = hasCustom
                    ? count
                      ? `${count} + custom`
                      : 'custom'
                    : `${count} selected`
                  return (
                    <button
                      key={`chip-${key}`}
                      type="button"
                      className="inline-flex items-center gap-2 rounded-full bg-white border border-gray-200 px-3 py-1 text-xs text-gray-700 shadow-sm hover:border-gray-400"
                      onClick={() => clearColumnFilter(key)}
                    >
                      <span className="font-semibold text-gray-900">{label}:</span>
                      <span>{summary}</span>
                      <X className="w-3 h-3" />
                    </button>
                  )
                })}
                <button
                  type="button"
                  className="text-xs text-gray-600 underline decoration-dotted hover:text-gray-900"
                  onClick={clearAllColumnFilters}
                >
                  Clear column filters
                </button>
              </div>
            )}

            {fetchError && (
              <div className="px-6 py-3 bg-red-50 text-sm text-red-700 flex items-center gap-2">
                <AlertCircle className="w-4 h-4" />
                {fetchError}
              </div>
            )}

            <div className="flex-1 overflow-auto">
              {loading ? (
                <div className="flex items-center justify-center py-12 text-gray-500 text-sm">
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Loading staged papers...
                </div>
              ) : rows.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-16 text-center px-6">
                  <p className="text-lg font-semibold text-gray-800 mb-2">
                    {stats.totalRows > 0 ? 'No papers match your current filters' : 'No papers staged yet'}
                  </p>
                  <p className="text-sm text-gray-500 mb-4">
                    {stats.totalRows > 0
                      ? 'Try adjusting the filters to see more staged papers.'
                      : 'Use “Add more papers” to bring in seeds from manual IDs or other sources.'}
                  </p>
                  {stats.totalRows === 0 ? (
                    <div className="flex flex-col sm:flex-row gap-3 w-full max-w-md">
                      <Button
                        variant="outline"
                        className="rounded-full flex-1"
                        onClick={() => setManualModalOpen(true)}
                      >
                        Manual IDs
                      </Button>
                      <Button
                        variant="outline"
                        className="rounded-full flex-1"
                        onClick={() => setShowZoteroModal(true)}
                      >
                        Zotero collections
                      </Button>
                      <Button
                        variant="outline"
                        className="rounded-full flex-1"
                        onClick={() => setShowPdfModal(true)}
                      >
                        Dump files
                      </Button>
                    </div>
                  ) : (
                    <Button
                      variant="outline"
                      className="rounded-full"
                      onClick={resetFilters}
                    >
                      Clear filters
                    </Button>
                  )}
                </div>
              ) : (
                <table className="min-w-full divide-y divide-gray-100">
                  <thead className="bg-gray-50 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                    <tr>
                      <th className="px-4 py-3">
                        <input
                          type="checkbox"
                          className="rounded border-gray-300 text-gray-900 focus:ring-gray-900"
                          checked={rows.every((row) => row.is_selected)}
                          onChange={(e) => handleSelectVisible(e.target.checked)}
                        />
                      </th>
                      <SortableHead label="Source" field="source" sort={sort} onToggle={toggleSort} />
                      <SortableHead
                        label="Title"
                        field="title"
                        sort={sort}
                        onToggle={toggleSort}
                        filterKey="title"
                        filterOptions={columnOptions.title}
                        selectedFilters={columnFilters.title}
                        customFilter={columnCustomFilters.title}
                        onApplyFilter={handleColumnFilterApply}
                        onApplyCustomFilter={handleColumnCustomFilterApply}
                      />
                      <SortableHead
                        label="Authors"
                        field="authors"
                        sort={sort}
                        onToggle={toggleSort}
                        filterKey="authors"
                        filterOptions={columnOptions.authors}
                        selectedFilters={columnFilters.authors}
                        customFilter={columnCustomFilters.authors}
                        onApplyFilter={handleColumnFilterApply}
                        onApplyCustomFilter={handleColumnCustomFilterApply}
                      />
                      <SortableHead
                        label="Year"
                        field="year"
                        sort={sort}
                        onToggle={toggleSort}
                        filterKey="year"
                        filterOptions={columnOptions.year}
                        selectedFilters={columnFilters.year}
                        customFilter={columnCustomFilters.year}
                        onApplyFilter={handleColumnFilterApply}
                        onApplyCustomFilter={handleColumnCustomFilterApply}
                      />
                      <SortableHead
                        label="Venue"
                        field="venue"
                        sort={sort}
                        onToggle={toggleSort}
                        filterKey="venue"
                        filterOptions={columnOptions.venue}
                        selectedFilters={columnFilters.venue}
                        customFilter={columnCustomFilters.venue}
                        onApplyFilter={handleColumnFilterApply}
                        onApplyCustomFilter={handleColumnCustomFilterApply}
                      />
                      <SortableHead
                        label="Identifiers"
                        sort={sort}
                        onToggle={null}
                        filterKey="identifier"
                        filterOptions={columnOptions.identifier}
                        selectedFilters={columnFilters.identifier}
                        customFilter={columnCustomFilters.identifier}
                        onApplyFilter={handleColumnFilterApply}
                        onApplyCustomFilter={handleColumnCustomFilterApply}
                      />
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {rows.map((row) => (
                      <tr
                        key={row.staging_id}
                        className={`transition-colors ${row.is_selected ? 'bg-purple-50/70' : 'bg-white hover:bg-gray-50'}`}
                      >
                        <td className="px-4 py-3 align-top">
                          <input
                            type="checkbox"
                            className="rounded border-gray-300 text-gray-900 focus:ring-gray-900"
                            checked={row.is_selected}
                            onChange={(e) => handleSelectRow(row.staging_id, e.target.checked)}
                          />
                        </td>
                        <td className="px-4 py-3 align-top">
                          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-gray-100 text-xs font-semibold text-gray-700 mb-1">
                            {row.source || '—'}
                          </div>
                          {row.source_type &&
                            !['manual', 'pdf', 'zotero'].includes(row.source_type) &&
                            row.source_type !== row.source && (
                            <div className="text-xs text-gray-500 uppercase tracking-wide">
                              {row.source_type}
                            </div>
                          )}
                        </td>
                        <td className="px-4 py-3 align-top min-w-[220px]">
                          <div className="font-semibold text-gray-900 text-sm mb-1">
                            {renderEditableValue(row, 'title', 'Double-click to add title')}
                          </div>
                          {row.abstract ? (
                            <div className="text-xs text-gray-500 line-clamp-2">
                              {renderEditableValue(row, 'abstract', 'Double-click to add abstract', true)}
                            </div>
                          ) : (
                            <div className="text-xs text-gray-400">
                              {renderEditableValue(row, 'abstract', 'Double-click to add abstract', true)}
                            </div>
                          )}
                        </td>
                        <td className="px-4 py-3 align-top text-sm text-gray-700 min-w-[200px]">
                          {renderEditableValue(row, 'authors', 'Double-click to add authors')}
                        </td>
                        <td className="px-4 py-3 align-top text-sm text-gray-700 w-24 min-w-[96px]">
                          {renderEditableValue(row, 'year', 'Year')}
                        </td>
                        <td className="px-4 py-3 align-top text-sm text-gray-700 min-w-[180px]">
                          {renderEditableValue(row, 'venue', 'Double-click to add venue')}
                        </td>
                        <td className="px-4 py-3 align-top text-xs text-gray-600 space-y-2">
                          <div>
                            <div className="text-[10px] uppercase text-gray-400 mb-1">DOI</div>
                            {renderEditableValue(row, 'doi', 'Add DOI')}
                          </div>
                          <div>
                            <div className="text-[10px] uppercase text-gray-400 mb-1">URL</div>
                            {renderEditableValue(row, 'url', 'Add URL')}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>

            {rows.length > 0 && (
              <div className="border-t border-gray-100 px-6 py-4 flex items-center justify-between text-sm text-gray-600">
                <div>
                  Page {page} of {totalPages}
                </div>
                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    className="rounded-full text-xs"
                    disabled={page <= 1}
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                  >
                    Previous
                  </Button>
                  <Button
                    variant="outline"
                    className="rounded-full text-xs"
                    disabled={page >= totalPages}
                    onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  >
                    Next
                  </Button>
                </div>
              </div>
            )}
          </section>
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
          setGrobidStatus(defaultGrobidStatus)
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
            const stage = await apiClient(
              'POST',
              `${endpoints.seedsSession}/${sessionId}/pdfs/${uploadId}/stage`
            )
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

function SortableHead({
  label,
  field,
  sort,
  onToggle,
  filterKey,
  filterOptions,
  selectedFilters,
  customFilter,
  onApplyFilter,
  onApplyCustomFilter,
}) {
  const isSortable = Boolean(field && onToggle)
  const isActive = isSortable && sort.field === field
  const handleSort = () => {
    if (!isSortable) return
    onToggle(field)
  }
  return (
    <th className="px-4 py-3 text-left select-none">
      <div className="flex items-center gap-2 text-xs font-semibold text-gray-500 uppercase tracking-wider">
        <button
          type="button"
          className={`inline-flex items-center gap-1 ${
            isSortable ? 'text-gray-600 hover:text-gray-900' : 'cursor-default text-gray-400'
          }`}
          onClick={handleSort}
          disabled={!isSortable}
        >
          <span>{label}</span>
          {isActive && <span>{sort.direction === 'asc' ? '↑' : '↓'}</span>}
        </button>
        {filterKey ? (
          <ColumnFilterButton
            columnKey={filterKey}
            label={label}
            options={filterOptions}
            selectedItems={selectedFilters}
            customFilter={customFilter}
            onApply={(values) => onApplyFilter?.(filterKey, values)}
            onApplyCustomFilter={(payload) => onApplyCustomFilter?.(filterKey, payload)}
            disableSelectAll={(filterOptions?.length || 0) > 100}
          />
        ) : null}
      </div>
    </th>
  )
}


function ColumnFilterButton({
  columnKey,
  label,
  options = [],
  selectedItems = [],
  customFilter = null,
  onApply,
  onApplyCustomFilter,
  disableSelectAll = false,
}) {
  const [open, setOpen] = useState(false)
  const [searchValue, setSearchValue] = useState('')
  const [draftSelections, setDraftSelections] = useState(selectedItems)
  const [position, setPosition] = useState({ top: 0, left: 0 })
  const [startIndex, setStartIndex] = useState(0)
  const [mounted, setMounted] = useState(false)
  const [customDialogOpen, setCustomDialogOpen] = useState(false)
  const [customOperator, setCustomOperator] = useState('equals')
  const [customValue, setCustomValue] = useState('')
  const [customValueTo, setCustomValueTo] = useState('')
  const [customError, setCustomError] = useState('')
  const buttonRef = useRef(null)
  const popoverRef = useRef(null)
  const listRef = useRef(null)
  const selectAllRef = useRef(null)
  const columnType = getColumnType(columnKey)
  const availableOperations = columnType === 'number' ? NUMBER_FILTER_OPERATIONS : TEXT_FILTER_OPERATIONS
  const describeCustomFilter = (filter) => {
    if (!filter) return ''
    const operationLabel = FILTER_OPERATION_DESCRIPTIONS[filter.operator] || filter.operator
    if (filter.operator === 'between' || filter.operator === 'not_between') {
      const toValue = filter.valueTo ?? ''
      return `${label} ${operationLabel.toLowerCase()} ${filter.value} and ${toValue}`
    }
    return `${label} ${operationLabel.toLowerCase()} ${filter.value}`
  }
  useEffect(() => {
    setMounted(true)
  }, [])
  useEffect(() => {
    if (!open) return
    setDraftSelections(selectedItems || [])
    setSearchValue('')
    setStartIndex(0)
    if (listRef.current) listRef.current.scrollTop = 0
    if (buttonRef.current) {
      const rect = buttonRef.current.getBoundingClientRect()
      const width = 320
      const margin = 12
      const nextLeft = Math.min(Math.max(margin, rect.left), window.innerWidth - width - margin)
      const nextTop = Math.min(window.innerHeight - margin, rect.bottom + 8)
      setPosition({ top: nextTop, left: nextLeft })
    }
  }, [open, selectedItems])
  useEffect(() => {
    if (!open) return
    const handlePointerDown = (event) => {
      if (
        buttonRef.current?.contains(event.target) ||
        popoverRef.current?.contains(event.target)
      ) {
        return
      }
      setOpen(false)
    }
    const handleKeyDown = (event) => {
      if (event.key === 'Escape') setOpen(false)
    }
    const handleReposition = () => {
      if (!buttonRef.current) return
      const rect = buttonRef.current.getBoundingClientRect()
      const width = 320
      const margin = 12
      const nextLeft = Math.min(Math.max(margin, rect.left), window.innerWidth - width - margin)
      const nextTop = Math.min(window.innerHeight - margin, rect.bottom + 8)
      setPosition({ top: nextTop, left: nextLeft })
    }
    document.addEventListener('pointerdown', handlePointerDown)
    document.addEventListener('keydown', handleKeyDown)
    window.addEventListener('resize', handleReposition)
    window.addEventListener('scroll', handleReposition, true)
    return () => {
      document.removeEventListener('pointerdown', handlePointerDown)
      document.removeEventListener('keydown', handleKeyDown)
      window.removeEventListener('resize', handleReposition)
      window.removeEventListener('scroll', handleReposition, true)
    }
  }, [open])
  useEffect(() => {
    if (!customDialogOpen) return
    const defaultOperator = customFilter?.operator || availableOperations[0]?.value || 'equals'
    setCustomOperator(defaultOperator)
    setCustomValue(customFilter?.value ?? '')
    setCustomValueTo(customFilter?.valueTo ?? '')
    setCustomError('')
  }, [customDialogOpen, customFilter, availableOperations])

  const filteredOptions = useMemo(() => {
    if (!searchValue) return options || []
    const lower = searchValue.toLowerCase()
    return (options || []).filter((opt) => (opt.label || '').toLowerCase().includes(lower))
  }, [options, searchValue])
  const selectedValueSet = useMemo(
    () => new Set((draftSelections || []).map((item) => item.value)),
    [draftSelections]
  )
  const totalFiltered = filteredOptions.length
  const visibleCount = 12
  const sliceStart = Math.min(startIndex, Math.max(0, totalFiltered - visibleCount))
  const sliceEnd = Math.min(totalFiltered, sliceStart + visibleCount)
  const visibleOptions = filteredOptions.slice(sliceStart, sliceEnd)
  const paddingTop = sliceStart * 36
  const paddingBottom = Math.max(0, (totalFiltered - sliceEnd) * 36)
  const selectionCount = draftSelections?.length || 0
  const badgeCount = selectionCount + (customFilter ? 1 : 0)
  const allFilteredSelected = totalFiltered > 0 && filteredOptions.every((opt) => selectedValueSet.has(opt.value))
  const someFilteredSelected = filteredOptions.some((opt) => selectedValueSet.has(opt.value))
  const isBetweenOperation = customOperator === 'between' || customOperator === 'not_between'
  useEffect(() => {
    if (!selectAllRef.current) return
    selectAllRef.current.indeterminate = !disableSelectAll && someFilteredSelected && !allFilteredSelected
  }, [disableSelectAll, someFilteredSelected, allFilteredSelected])
  const toggleOption = (option) => {
    setDraftSelections((prev) => {
      const exists = (prev || []).some((item) => item.value === option.value)
      if (exists) {
        return prev.filter((item) => item.value !== option.value)
      }
      return [...prev, { value: option.value, label: option.label, meta: option.meta || null }]
    })
  }
  const handleSelectAll = (event) => {
    if (disableSelectAll) return
    const checked = event.target.checked
    setDraftSelections((prev) => {
      const map = new Map((prev || []).map((item) => [item.value, item]))
      if (checked) {
        filteredOptions.forEach((option) => {
          if (!map.has(option.value)) {
            map.set(option.value, {
              value: option.value,
              label: option.label,
              meta: option.meta || null,
            })
          }
        })
      } else {
        filteredOptions.forEach((option) => map.delete(option.value))
      }
      return Array.from(map.values())
    })
  }
  const handleApplySelections = () => {
    onApply?.(draftSelections)
    setOpen(false)
  }
  const handleClearSelections = () => {
    onApply?.([])
    setOpen(false)
  }
  const handleClearCustom = () => {
    onApplyCustomFilter?.(null)
  }
  const handleCustomSave = () => {
    if (!customOperator) {
      setCustomError('Select an operation')
      return
    }
    const trimmedValue = `${customValue}`.trim()
    if (!trimmedValue) {
      setCustomError('Enter a value')
      return
    }
    if (columnType === 'number' && Number.isNaN(Number(trimmedValue))) {
      setCustomError('Enter a valid number')
      return
    }
    let trimmedValueTo = ''
    if (isBetweenOperation) {
      trimmedValueTo = `${customValueTo}`.trim()
      if (!trimmedValueTo) {
        setCustomError('Enter both values')
        return
      }
      if (columnType === 'number' && Number.isNaN(Number(trimmedValueTo))) {
        setCustomError('Enter a valid range')
        return
      }
    }
    onApplyCustomFilter?.({
      operator: customOperator,
      value: trimmedValue,
      valueTo: isBetweenOperation ? trimmedValueTo : null,
    })
    setCustomDialogOpen(false)
  }
  const listContent =
    visibleOptions.length === 0 ? (
      <div className="text-center text-sm text-gray-500 py-4">No values match this search.</div>
    ) : (
      <div style={{ paddingTop, paddingBottom }}>
        {visibleOptions.map((option) => (
          <label
            key={option.value}
            className="flex items-center justify-between gap-2 px-2 py-1.5 text-sm text-gray-700"
          >
            <div className="flex items-center gap-2 min-w-0">
              <input
                type="checkbox"
                className="rounded border-gray-300 text-gray-900 focus:ring-gray-900"
                checked={selectedValueSet.has(option.value)}
                onChange={() => toggleOption(option)}
              />
              <span className="truncate">{option.label}</span>
              {option.meta?.type && (
                <span className="text-[10px] uppercase text-gray-400 rounded-full border border-gray-200 px-2 py-0.5">
                  {option.meta.type}
                </span>
              )}
            </div>
            <span className="text-xs text-gray-400">{option.count?.toLocaleString?.() || option.count || 0}</span>
          </label>
        ))}
      </div>
    )
  if (!mounted) {
    return (
      <button
        type="button"
        ref={buttonRef}
        aria-label={`Filter ${label}`}
        className="inline-flex items-center justify-center rounded-full border border-gray-200 p-1 text-gray-500 hover:bg-gray-100"
        onClick={() => setOpen((prev) => !prev)}
      >
        <Filter className="w-3.5 h-3.5" />
      </button>
    )
  }
  return (
    <>
      <div className="relative">
        <button
          type="button"
          ref={buttonRef}
          aria-label={`Filter ${label}`}
          className={`relative inline-flex items-center justify-center rounded-full border p-1 transition ${
            badgeCount ? 'bg-gray-900 text-white border-gray-900' : 'border-gray-200 text-gray-500 hover:bg-gray-100'
          }`}
          onClick={() => setOpen((prev) => !prev)}
        >
          <Filter className="w-3.5 h-3.5" />
          {badgeCount > 0 && (
            <span className="absolute -top-1 -right-1 rounded-full bg-white text-gray-900 text-[10px] font-semibold px-1">
              {badgeCount}
            </span>
          )}
        </button>
        {open &&
          createPortal(
            <div
              ref={popoverRef}
              className="fixed z-50 w-80 rounded-3xl border border-gray-200 bg-white shadow-2xl p-4 space-y-3"
              style={{ top: position.top, left: position.left }}
            >
              <div className="flex items-center justify-between text-xs text-gray-500">
                <span className="font-semibold text-gray-900">{label} filters</span>
                <span>{selectionCount} selected</span>
              </div>
              <input
                type="text"
                className="w-full rounded-full border border-gray-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-gray-900"
                placeholder={`Search ${label.toLowerCase()}`}
                value={searchValue}
                onChange={(e) => setSearchValue(e.target.value)}
              />
              <div className="flex items-center justify-between text-xs text-gray-600">
                <label className="inline-flex items-center gap-2">
                  <input
                    type="checkbox"
                    ref={selectAllRef}
                    className="rounded border-gray-300 text-gray-900 focus:ring-gray-900"
                    disabled={disableSelectAll || filteredOptions.length === 0}
                    checked={!disableSelectAll && filteredOptions.length > 0 && allFilteredSelected}
                    onChange={handleSelectAll}
                  />
                  <span>Select all</span>
                </label>
                {disableSelectAll && (
                  <span className="text-[11px] text-gray-400">Disabled for large lists</span>
                )}
              </div>
              <div
                ref={listRef}
                className="max-h-60 overflow-y-auto border border-gray-100 rounded-2xl"
                onScroll={(event) => {
                  const newIndex = Math.floor(event.currentTarget.scrollTop / 36)
                  if (newIndex !== startIndex) setStartIndex(newIndex)
                }}
              >
                {listContent}
              </div>
              {customFilter ? (
                <div className="rounded-2xl bg-gray-50 px-3 py-2 text-[11px] text-gray-600 flex items-center justify-between gap-3">
                  <span className="truncate">{describeCustomFilter(customFilter)}</span>
                  <button
                    type="button"
                    className="text-gray-500 hover:text-gray-900 font-semibold"
                    onClick={handleClearCustom}
                  >
                    Clear
                  </button>
                </div>
              ) : null}
              <button
                type="button"
                className="text-xs text-gray-600 underline decoration-dotted hover:text-gray-900"
                onClick={() => setCustomDialogOpen(true)}
              >
                Custom filter…
              </button>
              <div className="flex items-center justify-between gap-3 pt-2 border-t border-gray-100">
                <Button
                  type="button"
                  variant="outline"
                  className="rounded-full px-4 text-xs"
                  onClick={handleClearSelections}
                >
                  Clear
                </Button>
                <Button
                  type="button"
                  className="rounded-full px-4 text-xs bg-gray-900 text-white"
                  onClick={handleApplySelections}
                >
                  Apply
                </Button>
              </div>
            </div>,
            document.body
          )}
      </div>
      <Dialog open={customDialogOpen} onOpenChange={setCustomDialogOpen}>
        <DialogContent className="sm:max-w-md bg-white p-6 rounded-3xl border-0 shadow-2xl">
          <DialogHeader className="pb-2">
            <DialogTitle>Custom filter for {label}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 text-sm text-gray-600">
            <div className="text-xs uppercase tracking-wider text-gray-500">
              Show items where: <span className="text-gray-900 normal-case">{label.toLowerCase()}</span>
            </div>
            <div>
              <label className="text-xs uppercase tracking-wider text-gray-500 mb-1 block">Operation</label>
              <Select
                value={customOperator}
                onValueChange={(value) => {
                  setCustomOperator(value)
                  if (value !== 'between' && value !== 'not_between') {
                    setCustomValueTo('')
                  }
                }}
              >
                <SelectTrigger className="w-full rounded-full border border-gray-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-gray-900">
                  <SelectValue placeholder="Choose operation" />
                </SelectTrigger>
                <SelectContent className="rounded-2xl border border-gray-200 bg-white shadow-lg">
                  {availableOperations.map((operation) => (
                    <SelectItem key={operation.value} value={operation.value}>
                      {operation.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className={isBetweenOperation ? 'grid grid-cols-1 sm:grid-cols-2 gap-3' : ''}>
              <div>
                <label className="text-xs uppercase tracking-wider text-gray-500 mb-1 block">
                  {columnType === 'number' ? 'Value' : 'Text'}
                </label>
                <Input
                  type={columnType === 'number' ? 'number' : 'text'}
                  value={customValue}
                  onChange={(e) => setCustomValue(e.target.value)}
                  placeholder={columnType === 'number' ? 'e.g. 2020' : 'e.g. Nature'}
                  className="rounded-full"
                />
              </div>
              {isBetweenOperation ? (
                <div>
                  <label className="text-xs uppercase tracking-wider text-gray-500 mb-1 block">And</label>
                  <Input
                    type={columnType === 'number' ? 'number' : 'text'}
                    value={customValueTo}
                    onChange={(e) => setCustomValueTo(e.target.value)}
                    placeholder={columnType === 'number' ? 'e.g. 2024' : 'e.g. Sensors'}
                    className="rounded-full"
                  />
                </div>
              ) : null}
            </div>
            {customError && <p className="text-xs text-red-600">{customError}</p>}
            <div className="flex justify-end gap-3 pt-2">
              <Button
                type="button"
                variant="outline"
                className="rounded-full px-4 text-xs"
                onClick={() => setCustomDialogOpen(false)}
              >
                Cancel
              </Button>
              <Button
                type="button"
                className="rounded-full px-4 text-xs bg-gray-900 text-white"
                onClick={handleCustomSave}
              >
                OK
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </>
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

function ZoteroCollectionsModal({
  open,
  onClose,
  collections,
  selected,
  setSelected,
  loading,
  error,
  onConfirm,
  onOpenSettings,
}) {
  const toggle = (key) => {
    setSelected((prev) => ({ ...prev, [key]: !prev[key] }))
  }
  const allSelected = collections.length > 0 && collections.every((c) => selected[c.key])
  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-2xl bg-white p-0 gap-0 rounded-3xl border-0 shadow-2xl">
        <DialogHeader className="px-6 pt-6 pb-2">
          <DialogTitle>Import from Zotero</DialogTitle>
        </DialogHeader>
        <div className="px-6 pb-6 space-y-4">
          <div className="flex items-center justify-between text-sm">
            <Button
              variant="ghost"
              className="rounded-full px-4"
              onClick={() => {
                const next = {}
                collections.forEach((c) => { next[c.key] = true })
                setSelected(next)
              }}
            >
              Select all
            </Button>
            <Button
              variant="ghost"
              className="rounded-full px-4"
              onClick={() => {
                const next = {}
                collections.forEach((c) => { next[c.key] = false })
                setSelected(next)
              }}
            >
              Clear
            </Button>
          </div>
          <div className="max-h-80 overflow-y-auto border border-gray-100 rounded-2xl divide-y">
            {collections.map((collection) => (
              <label key={collection.key} className="flex items-center gap-3 px-4 py-3 text-sm">
                <input
                  type="checkbox"
                  className="rounded border-gray-300 text-gray-900 focus:ring-gray-900"
                  checked={!!selected[collection.key]}
                  onChange={() => toggle(collection.key)}
                />
                <div>
                  <div className="font-semibold text-gray-900">{collection.name}</div>
                  <div className="text-xs text-gray-500">Key: {collection.key}</div>
                </div>
              </label>
            ))}
            {!collections.length && (
              <div className="px-4 py-6 text-sm text-gray-500">No collections available.</div>
            )}
          </div>
          {error && (
            <div className="text-sm text-red-600 space-y-2">
              <p>{error}</p>
              {onOpenSettings && (
                <Button
                  type="button"
                  variant="ghost"
                  className="rounded-full px-4 text-xs text-red-600 hover:text-red-700 border border-red-100"
                  onClick={onOpenSettings}
                >
                  Update Zotero settings
                </Button>
              )}
            </div>
          )}
          <div className="flex justify-end gap-3">
            <Button variant="outline" className="rounded-full px-6" onClick={onClose} disabled={loading}>
              Cancel
            </Button>
            <Button
              className="rounded-full px-6 bg-gray-900 text-white hover:bg-gray-800 disabled:opacity-60"
              onClick={onConfirm}
              disabled={loading || collections.length === 0 || (!allSelected && !Object.values(selected).some(Boolean))}
            >
              {loading ? 'Importing…' : 'Import selected'}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}

function PdfUploadModal({
  open,
  onClose,
  files,
  setFiles,
  loading,
  error,
  onConfirm,
  onOpenGrobidGuide,
  grobidStatus,
}) {
  const onFileChange = (event) => {
    const list = Array.from(event.target.files || [])
    setFiles(list)
  }
  const grobidError =
    typeof error === 'string' &&
    error.toLowerCase().includes('grobid') &&
    error.toLowerCase().includes('service is not running')
  const grobidWarningMessage =
    grobidStatus?.checked && grobidStatus.available === false
      ? grobidStatus?.message ||
        'GROBID service is not running. Please start it before uploading PDF files.'
      : null
  const showGrobidGuideButton = Boolean((grobidWarningMessage || grobidError) && onOpenGrobidGuide)
  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-2xl bg-white p-0 gap-0 rounded-3xl border-0 shadow-2xl">
        <DialogHeader className="px-6 pt-6 pb-2">
          <DialogTitle>Import from dump files</DialogTitle>
        </DialogHeader>
        <div className="px-6 pb-6 space-y-4">
          <div className="border-2 border-dashed border-gray-300 rounded-2xl p-6 text-center space-y-3">
            <p className="text-sm text-gray-600">
              Drop document files (PDF, DOCX, HTML, XML, LaTeX) here or browse
            </p>
            <div className="flex flex-col sm:flex-row gap-3 justify-center">
              <label className="inline-flex items-center gap-2 px-4 py-2 rounded-full border border-gray-300 cursor-pointer hover:bg-gray-50">
                <input
                  type="file"
                  multiple
                  accept=".pdf,.docx,.html,.htm,.xml,.tex"
                  onChange={onFileChange}
                  className="hidden"
                />
                <span className="text-sm font-medium text-gray-700">Browse files</span>
              </label>
              <label className="inline-flex items-center gap-2 px-4 py-2 rounded-full border border-gray-300 cursor-pointer hover:bg-gray-50">
                <input
                  type="file"
                  multiple
                  accept=".pdf,.docx,.html,.htm,.xml,.tex"
                  webkitdirectory=""
                  directory=""
                  onChange={onFileChange}
                  className="hidden"
                />
                <span className="text-sm font-medium text-gray-700">Select folder</span>
              </label>
            </div>
            <p className="text-xs text-gray-400">
              PDFs still require GROBID; other formats extract without it. Folder selection is available on Chromium-based browsers.
            </p>
          </div>
          {files.length > 0 && (
            <div className="max-h-48 overflow-y-auto border border-gray-100 rounded-2xl">
              {files.map((file) => (
                <div key={file.name} className="px-4 py-2 text-sm text-gray-700 border-b last:border-b-0">
                  {file.name} ({(file.size / (1024 * 1024)).toFixed(2)} MB)
                </div>
              ))}
            </div>
          )}
          {grobidWarningMessage && (
            <div className="text-sm text-red-600 space-y-2">
              <p>{grobidWarningMessage}</p>
              {showGrobidGuideButton && (
                <Button
                  type="button"
                  variant="ghost"
                  className="rounded-full px-4 text-xs text-red-600 hover:text-red-700 border border-red-100"
                  onClick={onOpenGrobidGuide}
                >
                  View GROBID setup guide
                </Button>
              )}
            </div>
          )}
          {error && (
            <div className="text-sm text-red-600 space-y-2">
              <p>{error}</p>
              {!grobidWarningMessage && grobidError && onOpenGrobidGuide && (
                <Button
                  type="button"
                  variant="ghost"
                  className="rounded-full px-4 text-xs text-red-600 hover:text-red-700 border border-red-100"
                  onClick={onOpenGrobidGuide}
                >
                  View GROBID setup guide
                </Button>
              )}
            </div>
          )}
          <div className="flex justify-end gap-3">
            <Button variant="outline" className="rounded-full px-6" onClick={onClose} disabled={loading}>
              Cancel
            </Button>
            <Button
              className="rounded-full px-6 bg-gray-900 text-white hover:bg-gray-800 disabled:opacity-60"
              onClick={onConfirm}
              disabled={loading || files.length === 0}
            >
              {loading ? 'Importing…' : 'Import PDFs'}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}
