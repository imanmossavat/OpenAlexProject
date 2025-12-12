import { useCallback, useEffect, useMemo, useState } from 'react'

import apiClient from '@/shared/api/client'
import { endpoints } from '@/shared/api/endpoints'
import {
  CATALOG_COLUMN_QUERY_MAP,
  CATALOG_FILTERABLE_COLUMNS,
  CATALOG_ANNOTATION_MARK_VALUES,
  createCatalogColumnCustomState,
  createCatalogColumnState,
} from '@/pages/crawler/results/catalogFilters'

const ALL_ANNOTATION_MARK_VALUES = CATALOG_ANNOTATION_MARK_VALUES || []

const DEFAULT_FILTERS = {
  search: '',
  venue: '',
  doiFilter: 'all',
  marks: [...ALL_ANNOTATION_MARK_VALUES],
  seedFilter: 'all',
  retractionFilter: 'all',
  topics: [],
  yearFrom: '',
  yearTo: '',
}

export const createDefaultCatalogFilters = () => ({
  ...DEFAULT_FILTERS,
  marks: [...DEFAULT_FILTERS.marks],
})

export default function useCrawlerPapers({
  jobId,
  pageSize = 25,
  enabled = true,
} = {}) {
  const [filters, setFilters] = useState(() => createDefaultCatalogFilters())
  const [page, setPage] = useState(1)
  const [internalPageSize, setInternalPageSize] = useState(pageSize)
  const [papers, setPapers] = useState([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [columnFilters, setColumnFilters] = useState(() => createCatalogColumnState())
  const [columnCustomFilters, setColumnCustomFilters] = useState(() => createCatalogColumnCustomState())
  const [columnOptions, setColumnOptions] = useState(() => createCatalogColumnState())
  const [sortState, setSortState] = useState({ key: 'centrality_out', direction: 'desc' })

  useEffect(() => {
    setInternalPageSize(pageSize)
  }, [pageSize])

  useEffect(() => {
    setPage(1)
    setPapers([])
    setTotal(0)
    setColumnFilters(createCatalogColumnState())
    setColumnCustomFilters(createCatalogColumnCustomState())
  }, [jobId])

  const columnValueQuery = useMemo(() => {
    const payload = {}
    Object.entries(CATALOG_COLUMN_QUERY_MAP).forEach(([columnKey, queryKey]) => {
      const values = columnFilters[columnKey] || []
      if (!values.length) return
      const cleanValues = values
        .map((item) => (item?.value || '').trim())
        .filter((value) => value.length > 0)
      if (!cleanValues.length) return
      payload[queryKey] = cleanValues
    })
    return payload
  }, [columnFilters])

  const columnCustomQuery = useMemo(() => {
    const payload = []
    CATALOG_FILTERABLE_COLUMNS.forEach(({ key }) => {
      const custom = columnCustomFilters[key]
      if (!custom || !custom.operator) return
      const value = `${custom.value ?? ''}`.trim()
      if (!value) return
      let entry = `${key}::${custom.operator}::${value}`
      if (custom.valueTo !== undefined && custom.valueTo !== null) {
        const secondary = `${custom.valueTo}`.trim()
        if (secondary) entry = `${entry}::${secondary}`
      }
      payload.push(entry)
    })
    return payload
  }, [columnCustomFilters])

  const activeQueryPayload = useMemo(() => {
    const trimmedSearch = (filters.search || '').trim()
    const trimmedVenue = (filters.venue || '').trim()
    const trimmedYearFrom = (filters.yearFrom || '').trim()
    const trimmedYearTo = (filters.yearTo || '').trim()
    const payload = {}

    if (trimmedSearch) payload.query = trimmedSearch
    if (trimmedVenue) payload.venue = trimmedVenue

    if (trimmedYearFrom) {
      const parsedFrom = Number.parseInt(trimmedYearFrom, 10)
      if (!Number.isNaN(parsedFrom)) payload.year_from = parsedFrom
    }
    if (trimmedYearTo) {
      const parsedTo = Number.parseInt(trimmedYearTo, 10)
      if (!Number.isNaN(parsedTo)) payload.year_to = parsedTo
    }

    const doiFilter = (filters.doiFilter || 'all').toLowerCase()
    if (doiFilter === 'with') payload.doi_filter = 'with'
    else if (doiFilter === 'without') payload.doi_filter = 'without'

    const seedFilter = (filters.seedFilter || 'all').toLowerCase()
    if (seedFilter === 'with') payload.seed_filter = 'with'
    else if (seedFilter === 'without') payload.seed_filter = 'without'

    const retractionFilter = (filters.retractionFilter || 'all').toLowerCase()
    if (retractionFilter === 'with') payload.retraction_filter = 'with'
    else if (retractionFilter === 'without') payload.retraction_filter = 'without'

    const selectedTopics = Array.isArray(filters.topics)
      ? Array.from(
          new Set(
            filters.topics
              .map((value) => {
                const parsed = Number.parseInt(`${value}`.trim(), 10)
                return Number.isNaN(parsed) ? null : parsed
              })
              .filter((value) => value !== null)
          )
        )
      : []
    if (selectedTopics.length) {
      payload.topic_ids = selectedTopics
    }

    const normalizedMarks = Array.isArray(filters.marks)
      ? Array.from(
          new Set(
            filters.marks
              .map((mark) => (mark || '').toLowerCase().trim())
              .filter(Boolean)
          )
        )
      : []
    if (normalizedMarks.length && normalizedMarks.length < ALL_ANNOTATION_MARK_VALUES.length) {
      payload.mark = normalizedMarks
    }

    Object.assign(payload, columnValueQuery)
    if (columnCustomQuery.length) {
      payload.column_filters = columnCustomQuery
    }

    return payload
  }, [filters, columnValueQuery, columnCustomQuery])

  const fetchPapers = useCallback(async () => {
    if (!jobId || !enabled) {
      setPapers([])
      setTotal(0)
      setLoading(false)
      return
    }

    setLoading(true)
    setError(null)
    const query = {
      page,
      page_size: internalPageSize,
    }
    Object.assign(query, activeQueryPayload)
    if (sortState?.key) {
      query.sort_by = sortState.key
      query.sort_dir = sortState.direction === 'asc' ? 'asc' : 'desc'
    }

    const res = await apiClient(
      'GET',
      `${endpoints.crawler}/jobs/${jobId}/papers`,
      undefined,
      { query }
    )

    if (res.error) {
      setError(res.error)
      setPapers([])
      setTotal(0)
      setLoading(false)
      return
    }

    const data = res.data || {}
    const list = Array.isArray(data.papers) ? data.papers : []
    const totalCount = typeof data.total === 'number' ? data.total : 0
    setPapers(list)
    setTotal(totalCount)
    const nextOptions = createCatalogColumnState()
    const rawOptions = data.column_options || {}
    CATALOG_FILTERABLE_COLUMNS.forEach(({ key }) => {
      const values = Array.isArray(rawOptions[key]) ? rawOptions[key] : []
      nextOptions[key] = values
    })
    setColumnOptions(nextOptions)

    const maxPage = totalCount > 0 ? Math.ceil(totalCount / internalPageSize) : 1
    if (page > maxPage) {
      setPage(maxPage)
    }

    setLoading(false)
  }, [jobId, enabled, page, internalPageSize, activeQueryPayload, sortState])

  useEffect(() => {
    fetchPapers()
  }, [fetchPapers])

  const updateFilter = useCallback((key, value) => {
    setFilters((prev) => {
      if (prev[key] === value) return prev
      return { ...prev, [key]: value }
    })
    setPage(1)
  }, [])

  const resetFilters = useCallback(() => {
    setFilters(createDefaultCatalogFilters())
    setColumnFilters(createCatalogColumnState())
    setColumnCustomFilters(createCatalogColumnCustomState())
    setPage(1)
  }, [])

  const updateSortState = useCallback((nextState) => {
    setSortState((prev) => {
      const resolved = typeof nextState === 'function' ? nextState(prev) : nextState
      if (!resolved || !resolved.key) return prev
      if (prev?.key === resolved.key && prev?.direction === resolved.direction) {
        return prev
      }
      return resolved
    })
    setPage(1)
  }, [])

  const setPageSize = useCallback((nextSize) => {
    if (!nextSize || nextSize === internalPageSize) return
    setInternalPageSize(nextSize)
    setPage(1)
  }, [internalPageSize])

  const applyColumnFilter = useCallback((columnKey, selections) => {
    setColumnFilters((prev) => {
      const next = { ...prev }
      const safeSelections = Array.isArray(selections) ? selections : []
      const deduped = []
      const seen = new Set()
      safeSelections.forEach((item) => {
        const value = (item?.value || '').trim()
        if (!value || seen.has(value)) return
        seen.add(value)
        deduped.push({
          value,
          label: item.label || value,
          meta: item.meta || null,
        })
      })
      next[columnKey] = deduped
      return next
    })
    setPage(1)
  }, [])

  const applyColumnCustomFilter = useCallback((columnKey, customPayload) => {
    setColumnCustomFilters((prev) => ({
      ...prev,
      [columnKey]: customPayload,
    }))
    setPage(1)
  }, [])

  const clearColumnFilter = useCallback((columnKey) => {
    setColumnFilters((prev) => ({ ...prev, [columnKey]: [] }))
    setColumnCustomFilters((prev) => ({ ...prev, [columnKey]: null }))
    setPage(1)
  }, [])

  const clearAllColumnFilters = useCallback(() => {
    setColumnFilters(createCatalogColumnState())
    setColumnCustomFilters(createCatalogColumnCustomState())
    setPage(1)
  }, [])

  const fetchColumnOptions = useCallback(
    async (
      columnKey,
      { search = '', page: optionPage = 1, pageSize: optionPageSize = 100 } = {}
    ) => {
      if (!jobId || !enabled) return { options: [], total: 0 }
      const trimmedSearch = search.trim()

      const columnParam = CATALOG_COLUMN_QUERY_MAP[columnKey]
      const queryPayload = { ...activeQueryPayload }
      if (columnParam && queryPayload[columnParam] !== undefined) {
        delete queryPayload[columnParam]
      }
      if (Array.isArray(queryPayload.column_filters)) {
        const filtered = queryPayload.column_filters.filter(
          (entry) => typeof entry === 'string' && !entry.toLowerCase().startsWith(`${columnKey}::`.toLowerCase())
        )
        if (filtered.length) {
          queryPayload.column_filters = filtered
        } else {
          delete queryPayload.column_filters
        }
      }

      const query = {
        column: columnKey,
        page: optionPage,
        page_size: optionPageSize,
        ...queryPayload,
      }

      if (trimmedSearch) {
        query.option_query = trimmedSearch
      }

      const res = await apiClient(
        'GET',
        `${endpoints.crawler}/jobs/${jobId}/papers/column-options`,
        undefined,
        { query }
      )

      if (res.error) {
        throw new Error(res.error)
      }

      const data = res.data || {}
      return {
        options: Array.isArray(data.options) ? data.options : [],
        total: typeof data.total === 'number' ? data.total : 0,
      }
    },
    [jobId, enabled, activeQueryPayload]
  )

  return {
    papers,
    total,
    loading,
    error,
    page,
    pageSize: internalPageSize,
    filters,
    setPage,
    setPageSize,
    updateFilter,
    resetFilters,
    refresh: fetchPapers,
    columnFilters,
    columnCustomFilters,
    columnOptions,
    applyColumnFilter,
    applyColumnCustomFilter,
    clearColumnFilter,
    clearAllColumnFilters,
    fetchColumnOptions,
    sortState,
    updateSortState,
  }
}
