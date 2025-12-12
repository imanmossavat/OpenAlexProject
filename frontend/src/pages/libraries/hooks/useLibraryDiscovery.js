import { useCallback, useEffect, useMemo, useState } from 'react'

import apiClient from '@/shared/api/client'
import { endpoints } from '@/shared/api/endpoints'

export default function useLibraryDiscovery({ pageSize = 8 } = {}) {
  const [libraries, setLibraries] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const [searchInput, setSearchInput] = useState('')
  const [activeQuery, setActiveQuery] = useState('')

  const loadLibraries = useCallback(async () => {
    setLoading(true)
    setError(null)
    const queryParams = { page, page_size: pageSize }
    if (activeQuery) queryParams.query = activeQuery
    const res = await apiClient('GET', `${endpoints.library}/discover`, undefined, {
      query: queryParams,
    })
    if (res.error) {
      setError(res.error)
      setLibraries([])
      setTotal(0)
    } else {
      const discovered = Array.isArray(res.data?.libraries) ? res.data.libraries : []
      setLibraries(discovered)
      setTotal(res.data?.total ?? discovered.length)
    }
    setLoading(false)
  }, [activeQuery, page, pageSize])

  useEffect(() => {
    loadLibraries()
  }, [loadLibraries])

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
    libraries,
    loading,
    error,
    page,
    total,
    pageSize,
    maxPage,
    hasNextPage,
    searchInput,
    setSearchInput,
    activeQuery,
    setActiveQuery,
    goToNextPage,
    clearSearch,
    reload: loadLibraries,
  }
}
