import { useCallback, useEffect, useState } from 'react'

import apiClient from '@/shared/api/client'
import { endpoints } from '@/shared/api/endpoints'

export default function useZoteroImport({ sessionId, navigate, onSuccess }) {
  const [showZoteroModal, setShowZoteroModal] = useState(false)
  const [zoteroCollections, setZoteroCollections] = useState([])
  const [selectedCollections, setSelectedCollections] = useState({})
  const [zoteroLoading, setZoteroLoading] = useState(false)
  const [zoteroError, setZoteroError] = useState(null)

  useEffect(() => {
    if (!showZoteroModal || !sessionId) return
    let isCancelled = false
    const loadCollections = async () => {
      setZoteroError(null)
      const res = await apiClient('GET', `${endpoints.seedsSession}/${sessionId}/zotero/collections`)
      if (isCancelled) return
      if (res.error) {
        setZoteroError(res.error)
      } else {
        const collections = res.data?.collections || []
        setZoteroCollections(collections)
        const defaults = {}
        collections.forEach((collection) => {
          defaults[collection.key] = false
        })
        setSelectedCollections((prev) => ({ ...defaults, ...prev }))
      }
    }
    loadCollections()
    return () => {
      isCancelled = true
    }
  }, [showZoteroModal, sessionId])

  const openZoteroModal = useCallback(() => {
    setShowZoteroModal(true)
    setZoteroError(null)
  }, [])

  const closeZoteroModal = useCallback(() => {
    setShowZoteroModal(false)
    setSelectedCollections({})
    setZoteroError(null)
  }, [])

  const handleOpenZoteroPicker = useCallback(async () => {
    if (!sessionId) return
    setZoteroError(null)
    const availability = await apiClient(
      'GET',
      `${endpoints.seedsSession}/${sessionId}/zotero/availability`
    )
    if (availability.error) {
      setZoteroError(availability.error)
      return
    }
    if (availability.data?.available) {
      openZoteroModal()
    } else {
      setZoteroError(availability.data?.message || 'Zotero is not configured yet.')
      navigate('/settings/integrations?provider=zotero')
    }
  }, [sessionId, navigate, openZoteroModal])

  const confirmZoteroImport = useCallback(async () => {
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
      closeZoteroModal()
      onSuccess?.()
    } catch (err) {
      setZoteroError(err.message || 'Failed to import from Zotero')
    }
    setZoteroLoading(false)
  }, [sessionId, selectedCollections, closeZoteroModal, onSuccess])

  return {
    showZoteroModal,
    openZoteroModal,
    closeZoteroModal,
    zoteroCollections,
    selectedCollections,
    setSelectedCollections,
    zoteroLoading,
    zoteroError,
    setZoteroError,
    handleOpenZoteroPicker,
    confirmZoteroImport,
  }
}
