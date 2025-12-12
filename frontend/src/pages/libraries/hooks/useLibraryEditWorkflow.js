import { useCallback, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import apiClient from '@/shared/api/client'
import { endpoints } from '@/shared/api/endpoints'
import { setSessionId } from '@/shared/lib/session'

export default function useLibraryEditWorkflow() {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const startEditing = useCallback(
    async ({ path, name, description }) => {
      if (!path) {
        setError('Library path is required.')
        return
      }
      setLoading(true)
      setError(null)
      try {
        const startRes = await apiClient('POST', `${endpoints.seedsSession}/start`, { use_case: 'library_edit' })
        if (startRes.error || !startRes.data?.session_id) {
          throw new Error(startRes.error || 'Unable to start edit session')
        }
        const sessionId = startRes.data.session_id

        const selectPayload = { path, name }
        if (description) selectPayload.description = description
        const selectRes = await apiClient('POST', `${endpoints.library}/${sessionId}/select`, selectPayload)
        if (selectRes.error) throw new Error(selectRes.error || 'Failed to attach library')

        const stageRes = await apiClient('POST', `${endpoints.library}/${sessionId}/edit/stage`)
        if (stageRes.error) throw new Error(stageRes.error || 'Unable to load library contents')

        setSessionId(sessionId, { useCase: 'library_edit' })
        navigate('/create/staging')
      } catch (err) {
        setError(err.message || 'Something went wrong starting the edit workflow.')
      } finally {
        setLoading(false)
      }
    },
    [navigate]
  )

  const clearError = useCallback(() => setError(null), [])

  return {
    startEditing,
    loading,
    error,
    clearError,
  }
}
