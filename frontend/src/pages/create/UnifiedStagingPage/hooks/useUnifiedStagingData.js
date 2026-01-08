import { useCallback, useEffect, useMemo, useState } from 'react'
import apiClient from '@/shared/api/client'
import { endpoints } from '@/shared/api/endpoints'
import {
  COLUMN_QUERY_MAP,
  EDITABLE_FIELDS,
  FILTERABLE_COLUMNS,
  createColumnCustomState,
  createColumnState,
  createDefaultFilters,
} from '../constants'

export function useUnifiedStagingData({ sessionId, pageSize = 25 }) {
  const [rows, setRows] = useState([])
  const [loading, setLoading] = useState(true)
  const [fetchError, setFetchError] = useState(null)
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [stats, setStats] = useState({ totalRows: 0, filteredRows: 0, selectedCount: 0, retractedCount: 0 })
  const [filters, setFilters] = useState(() => createDefaultFilters())
  const [sort, setSort] = useState({ field: null, direction: 'asc' })
  const [sourceOptions, setSourceOptions] = useState([])
  const [columnFilters, setColumnFilters] = useState(() => createColumnState())
  const [columnCustomFilters, setColumnCustomFilters] = useState(() => createColumnCustomState())
  const [columnOptions, setColumnOptions] = useState(() => createColumnState())
  const [editing, setEditing] = useState({ id: null, field: null, value: '' })

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

  const availableSources = useMemo(() => {
    const set = new Set(sourceOptions)
    filters.sources.forEach((value) => set.add(value))
    return Array.from(set).filter(Boolean).sort()
  }, [sourceOptions, filters.sources])

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
    if (filters.retraction === 'retracted') {
      query.retraction_status = 'retracted'
    } else if (filters.retraction === 'clean') {
      query.retraction_status = 'not_retracted'
    }
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
    const res = await apiClient('GET', `${endpoints.seedsSession}/${sessionId}/staging`, null, {
      query,
    })
    if (res.error) {
      setFetchError(res.error)
    } else {
      const data = res.data || {}
      setRows(data.rows || [])
      setStats({
        totalRows: data.total_rows || 0,
        filteredRows: data.filtered_rows || data.total_rows || 0,
        selectedCount: data.selected_count || 0,
        retractedCount: data.retracted_count || 0,
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
    filters.retraction,
    filters.yearMin,
    filters.yearMax,
    filters.sources,
    columnFilterValues,
    columnCustomFilters,
  ])

  useEffect(() => {
    fetchRows()
  }, [fetchRows])

  const resetFilters = useCallback(() => {
    setFilters(createDefaultFilters())
    setColumnFilters(createColumnState())
    setColumnCustomFilters(createColumnCustomState())
    setPage(1)
  }, [])

  const updateFilterField = useCallback((key, value) => {
    setFilters((prev) => ({ ...prev, [key]: value }))
    setPage(1)
  }, [])

  const handleColumnFilterApply = useCallback((columnKey, selections) => {
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
  }, [])

  const handleColumnCustomFilterApply = useCallback((columnKey, customPayload) => {
    setColumnCustomFilters((prev) => ({ ...prev, [columnKey]: customPayload }))
    setPage(1)
  }, [])

  const clearColumnFilter = useCallback((columnKey) => {
    setColumnFilters((prev) => ({ ...prev, [columnKey]: [] }))
    setColumnCustomFilters((prev) => ({ ...prev, [columnKey]: null }))
    setPage(1)
  }, [])

  const clearAllColumnFilters = useCallback(() => {
    setColumnFilters(createColumnState())
    setColumnCustomFilters(createColumnCustomState())
    setPage(1)
  }, [])

  const toggleSourceFilter = useCallback((value) => {
    setFilters((prev) => {
      const exists = prev.sources.includes(value)
      const nextSources = exists ? prev.sources.filter((s) => s !== value) : [...prev.sources, value]
      return { ...prev, sources: nextSources }
    })
    setPage(1)
  }, [])

  const startEditing = useCallback((rowId, field, value) => {
    if (!EDITABLE_FIELDS.includes(field)) return
    setEditing({ id: rowId, field, value: value ?? '' })
  }, [])

  const cancelEditing = useCallback(() => {
    setEditing({ id: null, field: null, value: '' })
  }, [])

  const updateEditingValue = useCallback((value) => {
    setEditing((prev) => ({ ...prev, value }))
  }, [])

  const commitEditing = useCallback(async () => {
    if (!editing.id || !editing.field || !sessionId) return
    const value = editing.value
    const payload = {}
    if (editing.field === 'year') {
      payload.year = value ? Number(value) : null
    } else {
      payload[editing.field] = value || null
    }
    await apiClient('PATCH', `${endpoints.seedsSession}/${sessionId}/staging/${editing.id}`, payload)
    setEditing({ id: null, field: null, value: '' })
    fetchRows()
  }, [editing, sessionId, fetchRows])

  const handleSelectRow = useCallback(
    async (rowId, checked) => {
      if (!sessionId) return
      await apiClient('POST', `${endpoints.seedsSession}/${sessionId}/staging/select`, {
        staging_ids: [rowId],
        is_selected: checked,
      })
      fetchRows()
    },
    [sessionId, fetchRows]
  )

  const handleSelectVisible = useCallback(
    async (checked) => {
      if (!rows.length || !sessionId) return
      await apiClient('POST', `${endpoints.seedsSession}/${sessionId}/staging/select`, {
        staging_ids: rows.map((row) => row.staging_id),
        is_selected: checked,
      })
      fetchRows()
    },
    [rows, sessionId, fetchRows]
  )

  const toggleSort = useCallback((field) => {
    setSort((prev) => {
      if (prev.field === field) {
        const nextDir = prev.direction === 'asc' ? 'desc' : 'asc'
        return { field, direction: nextDir }
      }
      return { field, direction: 'asc' }
    })
  }, [])

  const totalFilteredRows = stats.filteredRows || stats.totalRows || 0
  const hasRows = rows.length > 0
  const rangeStart = hasRows ? (page - 1) * pageSize + 1 : 0
  const rangeEnd = hasRows ? Math.min(rangeStart + rows.length - 1, totalFilteredRows) : 0
  const showInitialEmptyState = !loading && !fetchError && stats.totalRows === 0

  return {
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
    setFilters,
    updateFilterField,
    columnFilters,
    columnCustomFilters,
    columnOptions,
    editing,
    pageSize,
    columnFilterValues,
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
  }
}
