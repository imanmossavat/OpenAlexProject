import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import apiClient from '@/shared/api/client'
import { endpoints } from '@/shared/api/endpoints'
import { getSessionId, hydrateSessionFromQuery } from '@/shared/lib/session'

export default function ManualIdsPage() {
  const [sessionId, setSessionId] = useState(null)
  const [mode, setMode] = useState('manual')
  const [idsText, setIdsText] = useState('')
  const [file, setFile] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const navigate = useNavigate()

  useEffect(() => {
    const sid = getSessionId() || hydrateSessionFromQuery()
    if (!sid) { navigate('/'); return }
    setSessionId(sid)
  }, [navigate])

  const onFile = (e) => {
    const f = e.target.files?.[0]
    setFile(f || null)
  }

  const addSeeds = async () => {
    if (!sessionId) return
    setLoading(true)
    setError(null)
    let paperIds = []
    if (mode === 'manual') {
      paperIds = idsText
        .split(/\r?\n/)
        .map((s) => s.trim())
        .filter(Boolean)
    } else if (mode === 'file' && file) {
      try {
        const text = await file.text()
        paperIds = text
          .split(/\r?\n/)
          .map((s) => s.trim())
          .filter(Boolean)
      } catch (e) {
        setError('Failed to read file')
        setLoading(false)
        return
      }
    }
    if (!paperIds.length) {
      setError('Please enter at least one Paper ID')
      setLoading(false)
      return
    }
    const res = await apiClient('POST', `${endpoints.seedsSession}/${sessionId}/paper-ids`, {
      paper_ids: paperIds,
      api_provider: 'openalex',
    })
    if (res.error) setError(res.error)
    else navigate('/create/seeds')
    setLoading(false)
  }

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-4">Add Seed Papers Manually</h1>
      {!sessionId && <div className="text-red-500 mb-4">Missing session. Start from Home → Create Library.</div>}

      <div className="flex gap-3 mb-4">
        <button
          className={`px-3 py-2 rounded ${mode === 'manual' ? 'bg-blue-600 text-white' : 'bg-gray-200'}`}
          onClick={() => setMode('manual')}
        >
          Enter manually
        </button>
        <button
          className={`px-3 py-2 rounded ${mode === 'file' ? 'bg-blue-600 text-white' : 'bg-gray-200'}`}
          onClick={() => setMode('file')}
        >
          Load IDs from file
        </button>
      </div>

      {mode === 'manual' ? (
        <textarea
          className="w-full border rounded p-2 h-48 mb-3"
          placeholder="One OpenAlex ID per line (e.g., W2741809807)"
          value={idsText}
          onChange={(e) => setIdsText(e.target.value)}
        />
      ) : (
        <input type="file" accept=".txt" onChange={onFile} className="mb-3" />
      )}
      <p className="text-sm text-gray-500 mb-3">
        Only OpenAlex IDs are supported in this importer. DOIs and other identifiers will be skipped.
      </p>

      <div className="flex gap-2">
        <button className="px-3 py-2 rounded bg-blue-600 text-white" onClick={addSeeds} disabled={loading}>
          Add seeds
        </button>
      </div>

      {loading && <div className="mt-3">Working...</div>}
      {error && <div className="mt-3 text-red-500">Error: {error}</div>}
    </div>
  )
}
