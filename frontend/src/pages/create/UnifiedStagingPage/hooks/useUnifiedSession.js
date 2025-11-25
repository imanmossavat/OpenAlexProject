import { useEffect, useState } from 'react'
import { getSessionId, hydrateSessionFromQuery } from '@/shared/lib/session'

export function useUnifiedSession(navigate) {
  const [sessionId, setSessionId] = useState(null)

  useEffect(() => {
    const sid = getSessionId() || hydrateSessionFromQuery()
    if (!sid) {
      navigate('/')
      return
    }
    setSessionId(sid)
  }, [navigate])

  return sessionId
}
