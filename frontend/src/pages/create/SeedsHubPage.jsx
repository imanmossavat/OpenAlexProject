import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import apiClient from '@/shared/api/client'
import { endpoints } from '@/shared/api/endpoints'
import { getSessionId, hydrateSessionFromQuery } from '@/shared/lib/session'

export default function SeedsHubPage() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const navigate = useNavigate()

  const [sessionId, setSessionIdState] = useState(null)

  useEffect(() => {
    const sid = getSessionId() || hydrateSessionFromQuery()
    if (!sid) { navigate('/'); return }
    setSessionIdState(sid)
    let mounted = true
    ;(async () => {
      const res = await apiClient('GET', `${endpoints.seedsSession}/${sid}`)
      if (!mounted) return
      if (res.error) setError(res.error)
      else setData(res.data)
      setLoading(false)
    })()
    return () => {
      mounted = false
    }
  }, [navigate])

  const finalize = async () => {
    if (!sessionId) return
    const res = await apiClient('POST', `${endpoints.seedsSession}/${sessionId}/finalize`)
    if (res.error) setError(res.error)
    else navigate('/create/details')
  }

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-4">Select Seed Papers</h1>
      <div className="flex gap-3 mb-6">
        <button className="px-3 py-2 rounded bg-gray-200" onClick={() => navigate('/create/seeds/zotero')}>
          Import from Zotero
        </button>
        <button className="px-3 py-2 rounded bg-gray-200" onClick={() => navigate('/create/seeds/pdf')}>
          Extract from PDF
        </button>
        <button className="px-3 py-2 rounded bg-gray-200" onClick={() => navigate('/create/seeds/manual')}>
          Enter Manually
        </button>
        <button className="ml-auto px-3 py-2 rounded bg-blue-600 text-white" onClick={finalize}>
          Done selecting seeds
        </button>
      </div>

      {loading && <div>Loading session seeds...</div>}
      {error && <div className="text-red-500">Error: {error}</div>}
      {!loading && !error && (
        <pre className="bg-gray-100 p-4 rounded overflow-auto">{JSON.stringify(data, null, 2)}</pre>
      )}
    </div>
  )
}
