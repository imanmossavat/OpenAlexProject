import { useCallback, useEffect, useMemo, useState } from 'react'

import apiClient from '@/shared/api/client'
import { endpoints } from '@/shared/api/endpoints'

import { isAbsolutePath } from '../utils'

export default function useLibraryRootPreference() {
  const [defaultRoot, setDefaultRoot] = useState(null)
  const [rootInput, setRootInput] = useState('')
  const [rootError, setRootError] = useState(null)
  const [rootLoading, setRootLoading] = useState(true)
  const [rootSaving, setRootSaving] = useState(false)

  const fetchDefaultRoot = useCallback(async () => {
    setRootLoading(true)
    setRootError(null)
    const res = await apiClient('GET', `${endpoints.settings}/library-root`)
    if (res.error) {
      setRootError(res.error)
      setDefaultRoot(null)
      setRootInput('')
    } else {
      const path = res.data?.path || ''
      setDefaultRoot(path || null)
      setRootInput(path)
    }
    setRootLoading(false)
  }, [])

  useEffect(() => {
    fetchDefaultRoot()
  }, [fetchDefaultRoot])

  const rootPathHasValue = rootInput.trim().length > 0
  const rootPathValid = useMemo(() => {
    if (!rootPathHasValue) return true
    return isAbsolutePath(rootInput)
  }, [rootInput, rootPathHasValue])

  const saveRoot = useCallback(async () => {
    if (!rootPathHasValue) {
      setRootError('Enter an absolute path.')
      return false
    }
    if (!isAbsolutePath(rootInput)) {
      setRootError('Default library path must be absolute.')
      return false
    }
    setRootSaving(true)
    setRootError(null)
    const payload = { path: rootInput.trim() }
    const res = await apiClient('PUT', `${endpoints.settings}/library-root`, payload)
    if (res.error) {
      setRootError(res.error)
      setRootSaving(false)
      return false
    }
    const path = res.data?.path || ''
    setDefaultRoot(path || null)
    setRootInput(path)
    setRootSaving(false)
    return true
  }, [rootInput, rootPathHasValue])

  const resetRoot = useCallback(async () => {
    setRootSaving(true)
    setRootError(null)
    const res = await apiClient('PUT', `${endpoints.settings}/library-root`, { path: null })
    if (res.error) {
      setRootError(res.error)
    } else {
      setDefaultRoot(null)
      setRootInput('')
    }
    setRootSaving(false)
  }, [])

  const clearRootError = useCallback(() => setRootError(null), [])

  return {
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
    refreshRoot: fetchDefaultRoot,
    clearRootError,
  }
}
