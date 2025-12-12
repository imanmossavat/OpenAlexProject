import { useCallback, useState } from 'react'

import apiClient from '@/shared/api/client'
import { endpoints } from '@/shared/api/endpoints'

export default function useManualIdImport({ sessionId, onSuccess }) {
  const [manualModalOpen, setManualModalOpen] = useState(false)
  const [manualIds, setManualIds] = useState('')
  const [manualSubmitting, setManualSubmitting] = useState(false)
  const [manualError, setManualError] = useState(null)

  const openManualModal = useCallback(() => {
    setManualModalOpen(true)
    setManualError(null)
  }, [])

  const closeManualModal = useCallback(() => {
    setManualModalOpen(false)
  }, [])

  const prepareManualPayload = useCallback(() => {
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
  }, [manualIds])

  const addManualRows = useCallback(async () => {
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
      onSuccess?.()
    }
  }, [sessionId, prepareManualPayload, onSuccess])

  return {
    manualModalOpen,
    openManualModal,
    closeManualModal,
    manualIds,
    setManualIds,
    manualSubmitting,
    manualError,
    addManualRows,
  }
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
