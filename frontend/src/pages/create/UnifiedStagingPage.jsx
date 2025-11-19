import { useCallback, useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { AlertCircle, Check, ChevronDown, Filter, Loader2, RefreshCw } from 'lucide-react'
import Stepper from '@/components/Stepper'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import apiClient from '@/shared/api/client'
import { endpoints } from '@/shared/api/endpoints'
import { getSessionId, hydrateSessionFromQuery } from '@/shared/lib/session'

const workflowSteps = ['Add', 'Stage', 'Match', 'Library']
const editableFields = ['title', 'authors', 'year', 'venue', 'doi', 'url', 'abstract']
const defaultGrobidStatus = { checked: false, available: true, message: null }

export default function UnifiedStagingPage() {
  const navigate = useNavigate()
  const [sessionId, setSessionId] = useState(null)
  const [rows, setRows] = useState([])
  const [loading, setLoading] = useState(true)
  const [fetchError, setFetchError] = useState(null)
  const [page, setPage] = useState(1)
  const [pageSize] = useState(25)
  const [totalPages, setTotalPages] = useState(1)
  const [stats, setStats] = useState({ totalRows: 0, selectedCount: 0 })
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
    const res = await apiClient('GET', `${endpoints.seedsSession}/${sessionId}/staging`, null, { query })
    if (res.error) {
      setFetchError(res.error)
    } else {
      const data = res.data || {}
      setRows(data.rows || [])
      setStats({
        totalRows: data.total_rows || 0,
        selectedCount: data.selected_count || 0,
      })
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

  const rangeStart = (page - 1) * pageSize + 1
  const rangeEnd = Math.min(rangeStart + rows.length - 1, stats.totalRows)

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

  return (
    <div className="min-h-screen bg-white flex flex-col">
      <div className="pt-8">
        <Stepper currentStep={2} steps={workflowSteps} />
      </div>

      <div className="px-6 pb-10 flex-1 flex flex-col">
        <header className="flex flex-wrap items-center justify-between gap-4 border border-gray-200 rounded-3xl px-6 py-4 bg-white shadow-md
">
          <div>
            <p className="text-sm uppercase tracking-[0.3em] text-gray-500 mb-1">Unified staging</p>
            <h1 className="text-2xl font-semibold text-gray-900">Manage all seed papers in a single table</h1>
          </div>
          <div className="flex items-center gap-2">
            <div className="text-sm text-gray-600">
              <span className="font-semibold text-gray-900">{stats.totalRows}</span> staged •{' '}
              <span className="font-semibold text-gray-900">{stats.selectedCount}</span> selected
            </div>
            <div className="relative">
              <Button
                variant="outline"
                className="rounded-full border-gray-300 text-gray-900"
                onClick={() => setShowAddMenu((prev) => !prev)}
              >
                Add more papers
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
            <Button
              className="rounded-full bg-gray-900 text-white hover:bg-gray-800 disabled:opacity-60"
              disabled={!stats.selectedCount || matching}
              onClick={runMatching}
            >
              {matching ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
              Done selecting seed papers
            </Button>
          </div>
        </header>

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
                  ? `Showing ${rangeStart}–${rangeEnd} of ${stats.totalRows} papers`
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
                      <SortableHead label="Title" field="title" sort={sort} onToggle={toggleSort} />
                      <SortableHead label="Authors" field="authors" sort={sort} onToggle={toggleSort} />
                      <SortableHead label="Year" field="year" sort={sort} onToggle={toggleSort} />
                      <SortableHead label="Venue" field="venue" sort={sort} onToggle={toggleSort} />
                      <th className="px-4 py-3">Identifiers</th>
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

function SortableHead({ label, field, sort, onToggle }) {
  const isActive = sort.field === field
  return (
    <th
      className="px-4 py-3 cursor-pointer select-none"
      onClick={() => onToggle(field)}
    >
      <div className="inline-flex items-center gap-1 text-xs font-semibold text-gray-500 uppercase tracking-wider">
        {label}
        {isActive && (
          <span>{sort.direction === 'asc' ? '↑' : '↓'}</span>
        )}
      </div>
    </th>
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
            <p className="text-sm text-gray-600">Drop PDF files here or browse</p>
            <div className="flex flex-col sm:flex-row gap-3 justify-center">
              <label className="inline-flex items-center gap-2 px-4 py-2 rounded-full border border-gray-300 cursor-pointer hover:bg-gray-50">
                <input
                  type="file"
                  multiple
                  accept="application/pdf"
                  onChange={onFileChange}
                  className="hidden"
                />
                <span className="text-sm font-medium text-gray-700">Browse files</span>
              </label>
              <label className="inline-flex items-center gap-2 px-4 py-2 rounded-full border border-gray-300 cursor-pointer hover:bg-gray-50">
                <input
                  type="file"
                  multiple
                  accept="application/pdf"
                  webkitdirectory=""
                  directory=""
                  onChange={onFileChange}
                  className="hidden"
                />
                <span className="text-sm font-medium text-gray-700">Select folder</span>
              </label>
            </div>
            <p className="text-xs text-gray-400">Folder selection is available on Chromium-based browsers.</p>
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
