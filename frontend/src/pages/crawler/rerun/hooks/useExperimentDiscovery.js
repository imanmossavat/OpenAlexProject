import { useCallback, useEffect, useMemo, useState } from 'react'

import apiClient from '@/shared/api/client'
import { endpoints } from '@/shared/api/endpoints'

export default function useExperimentDiscovery({ pageSize = 12 } = {}) {
  const [experiments, setExperiments] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const [rootPath, setRootPath] = useState(null)
  const [searchInput, setSearchInput] = useState('')
  const [activeQuery, setActiveQuery] = useState('')

  const loadExperiments = useCallback(async () => {
    setLoading(true)
    setError(null)
    const queryParams = { page, page_size: pageSize }
    if (activeQuery) queryParams.query = activeQuery
    const res = await apiClient('GET', `${endpoints.crawlerReruns}/experiments`, undefined, {
      query: queryParams,
    })
    if (res.error) {
      setError(res.error)
      setExperiments([])
      setTotal(0)
      setRootPath(null)
    } else {
      const rows = Array.isArray(res.data?.experiments) ? res.data.experiments : []
      setExperiments(rows)
      setTotal(res.data?.total ?? rows.length)
      setRootPath(res.data?.root_path || null)
    }
    setLoading(false)
  }, [activeQuery, page, pageSize])

  useEffect(() => {
    loadExperiments()
  }, [loadExperiments])

  useEffect(() => {
    const handle = setTimeout(() => {
      setPage(1)
      setActiveQuery(searchInput.trim())
    }, 400)
    return () => clearTimeout(handle)
  }, [searchInput])

  const maxPage = useMemo(() => (total > 0 ? Math.ceil(total / pageSize) : 1), [total, pageSize])
  const hasNextPage = page < maxPage

  const goToNextPage = useCallback(
    (direction) => {
      setPage((prev) => {
        const next = prev + direction
        if (next < 1) return 1
        if (next > maxPage) return maxPage
        return next
      })
    },
    [maxPage]
  )

  const clearSearch = useCallback(() => {
    setSearchInput('')
    if (activeQuery) {
      setActiveQuery('')
      setPage(1)
    }
  }, [activeQuery])

  return {
    experiments,
    loading,
    error,
    page,
    total,
    pageSize,
    hasNextPage,
    rootPath,
    searchInput,
    setSearchInput,
    activeQuery,
    goToNextPage,
    clearSearch,
    reload: loadExperiments,
  }
}
