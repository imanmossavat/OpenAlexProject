import { useCallback, useEffect, useState } from 'react'
import apiClient from '@/shared/api/client'
import { endpoints } from '@/shared/api/endpoints'
import { getSessionId, setSessionId } from '@/shared/lib/session'

export default function useCrawlerSession() {
  const [sessionId, setLocalSessionId] = useState(() => getSessionId())
  const [loading, setLoading] = useState(!sessionId)
  const [error, setError] = useState(null)

  const startSession = useCallback(async () => {
    setLoading(true)
    setError(null)
    const res = await apiClient('POST', `${endpoints.seedsSession}/start`, { use_case: 'crawler_wizard' })
    if (res.error || !res.data?.session_id) {
      setError(res.error || 'Unable to start crawler session')
      setLoading(false)
      return null
    }
    const newSessionId = res.data.session_id
    setSessionId(newSessionId)
    setLocalSessionId(newSessionId)
    setLoading(false)
    return newSessionId
  }, [])

  useEffect(() => {
    if (!sessionId) startSession()
  }, [sessionId, startSession])

  return {
    sessionId,
    loading,
    error,
    ensureSession: startSession,
  }
}
