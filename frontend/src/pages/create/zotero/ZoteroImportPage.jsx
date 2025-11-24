import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { X, ChevronDown, Search } from 'lucide-react'
import { Button } from '@/components/ui/button'
import apiClient from '@/shared/api/client'
import { endpoints } from '@/shared/api/endpoints'
import { getSessionId, hydrateSessionFromQuery } from '@/shared/lib/session'

export default function ZoteroImportPage() {
  const [sessionId, setSessionId] = useState(null)
  const [collections, setCollections] = useState([])
  const [selectedCollection, setSelectedCollection] = useState(null)
  const [items, setItems] = useState([])
  const [filter, setFilter] = useState({ q: '', type: '' })
  const [selectedItems, setSelectedItems] = useState({})
  const [staged, setStaged] = useState(null)
  const [matchRes, setMatchRes] = useState(null)
  const [manualSelections, setManualSelections] = useState({})
  const [reviewItem, setReviewItem] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const navigate = useNavigate()

  useEffect(() => {
    const sid = getSessionId() || hydrateSessionFromQuery()
    if (!sid) { navigate('/'); return }
    setSessionId(sid)
  }, [navigate])

  useEffect(() => {
    if (!sessionId) { setLoading(false); return }
    let mounted = true
    ;(async () => {
      const res = await apiClient('GET', `${endpoints.seedsSession}/${sessionId}/zotero/availability`)
      if (!mounted) return
      if (res.error) {
        setError(res.error)
        setLoading(false)
        return
      }
      if (!res.data?.available) {
        setError(res.data?.message || 'Zotero is not configured yet.')
        navigate('/settings/integrations?provider=zotero')
        setLoading(false)
        return
      }
      const cols = await apiClient('GET', `${endpoints.seedsSession}/${sessionId}/zotero/collections`)
      if (!cols.error) setCollections(cols.data?.collections || [])
      setLoading(false)
    })()
    return () => {
      mounted = false
    }
  }, [sessionId, navigate])

  const currentSid = () => getSessionId() || sessionId

  const filteredItems = useMemo(() => {
    const q = filter.q.toLowerCase()
    return (items || []).filter((it) => {
      const matchQ = !q || it.title?.toLowerCase().includes(q) || (it.authors || []).join(', ').toLowerCase().includes(q)
      const matchType = !filter.type || it.item_type === filter.type
      return matchQ && matchType
    })
  }, [items, filter])

  const loadItems = async (collection) => {
    setSelectedCollection(collection)
    setSelectedItems({})
    setItems([])
    setLoading(true)
    const sid = currentSid()
    const res = await apiClient('GET', `${endpoints.seedsSession}/${sid}/zotero/collections/${collection.key}/items`)
    if (res.error) setError(res.error)
    else setItems(res.data?.items || [])
    setLoading(false)
  }

  const toggleSelect = (key) => {
    setSelectedItems((prev) => ({ ...prev, [key]: !prev[key] }))
  }

  const stageSelected = async () => {
    if (!selectedCollection) return
    const sid = currentSid()
    const selected = Object.entries(selectedItems)
      .filter(([, v]) => v)
      .map(([k]) => k)
    const res = await apiClient('POST', `${endpoints.seedsSession}/${sid}/zotero/collections/${selectedCollection.key}/stage`, {
      action: 'stage_selected',
      selected_items: selected,
    })
    if (res.error) setError(res.error)
    else {
      await loadStaged()
      setSelectedItems({})
    }
  }

  const loadStaged = async () => {
    const sid = currentSid()
    const res = await apiClient('GET', `${endpoints.seedsSession}/${sid}/zotero/staged-items`)
    if (res.error) setError(res.error)
    else setStaged(res.data)
  }

  const removeStaged = async (keys) => {
    const sid = currentSid()
    for (const k of keys) {
      const r = await apiClient('DELETE', `${endpoints.seedsSession}/${sid}/zotero/staged-items/${k}`)
      if (r.error) {
        setError(r.error)
        return
      }
    }
    await loadStaged()
  }

  const startMatch = async () => {
    const sid = currentSid()
    const res = await apiClient('POST', `${endpoints.seedsSession}/${sid}/zotero/match`, {
      api_provider: 'openalex',
    })
    if (res.error) setError(res.error)
    else {
      setMatchRes(res.data)
      const unmatched = (res.data?.results || []).filter((r) => !r.matched)
      if (unmatched.length > 0) {
        setManualSelections((prev) => {
          const next = { ...prev }
          unmatched.forEach((r) => {
            if (!(r.zotero_key in next)) next[r.zotero_key] = ''
          })
          return next
        })
      }
    }
  }

  const confirmMatches = async () => {
    const sid = currentSid()
    const selections = Object.entries(manualSelections)
      .map(([zotero_key, selected_paper_id]) => ({ zotero_key, action: selected_paper_id ? 'select' : 'skip', selected_paper_id }))
    const res = await apiClient('POST', `${endpoints.seedsSession}/${sid}/zotero/confirm`, {
      action: 'accept_all',
      manual_selections: selections,
    })
    if (res.error) setError(res.error)
    else { navigate('/create/staging') }
  }

  const openReview = (item) => setReviewItem(item)
  const closeReview = () => setReviewItem(null)
  const chooseCandidate = (zotero_key, paper_id) => {
    setManualSelections((prev) => ({ ...prev, [zotero_key]: paper_id }))
    closeReview()
  }
  const skipCandidate = (zotero_key) => {
    setManualSelections((prev) => ({ ...prev, [zotero_key]: '' }))
    closeReview()
  }

  const selectedCount = Object.values(selectedItems).filter(Boolean).length
  const stagedCount = staged?.total_count || 0

  return (
    <div className="min-h-screen bg-white">
      {error && (
        <div className="bg-red-50 border-b border-red-200 px-6 py-3 text-red-700 text-sm">
          Error: {error}
        </div>
      )}

      <div className="flex h-[calc(100vh-0px)]">
        <div className="w-[20%] border-r border-gray-200 flex flex-col bg-white">
          <div className="text-lg font-semibold px-4 py-4 border-b border-gray-200">
            Your Collections
          </div>
          <div className="flex-1 overflow-auto">
            {loading && <div className="px-4 py-3 text-sm text-gray-500">Loading collections...</div>}
            {collections.map((c) => (
              <div
                key={c.key}
                className={`px-4 py-3 text-sm cursor-pointer transition-colors ${
                  selectedCollection?.key === c.key
                    ? 'bg-gray-100 border-l-4 border-l-purple-600 font-medium'
                    : 'hover:bg-gray-50'
                }`}
                onClick={() => loadItems(c)}
              >
                {c.name}
              </div>
            ))}
          </div>
        </div>

        <div className="w-[50%] border-r border-gray-200 flex flex-col bg-white">
          <div className="px-6 py-4 border-b border-gray-200">
            <div className="text-lg font-semibold">Papers</div>
          </div>

          <div className="flex items-center gap-3 px-6 py-3 border-b border-gray-200">
            <div className="relative flex-1">
              <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
              <input
  className="w-full border border-gray-300 rounded-full px-9 py-2 text-sm bg-white shadow-md hover:shadow-lg transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
  placeholder="Search..."
  value={filter.q}
  onChange={(e) => setFilter((f) => ({ ...f, q: e.target.value }))}
 />

              {filter.q && (
                <button
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                  onClick={() => setFilter((f) => ({ ...f, q: '' }))}
                >
                  <X className="w-4 h-4" />
                </button>
              )}
            </div>

             <button className="border border-gray-300 rounded-full px-4 py-2 text-sm inline-flex items-center gap-2 bg-white shadow-md hover:shadow-lg transition-all duration-200">
    All tags <ChevronDown className="w-4 h-4" />
  </button>
  <button className="border border-gray-300 rounded-full px-4 py-2 text-sm inline-flex items-center gap-2 bg-white shadow-md hover:shadow-lg transition-all duration-200">
    All paper types <ChevronDown className="w-4 h-4" />
  </button>
          </div>

          <div className="flex-1 overflow-auto">
            {!selectedCollection && (
              <div className="px-6 py-8 text-center text-gray-500 text-sm">Select a collection to view papers</div>
            )}
            {selectedCollection && loading && (
              <div className="px-6 py-8 text-center text-gray-500 text-sm">Loading papers...</div>
            )}
            {selectedCollection && !loading && filteredItems.length === 0 && (
              <div className="px-6 py-8 text-center text-gray-500 text-sm">No papers found</div>
            )}
            {filteredItems.map((it) => (
              <label
                key={it.zotero_key}
                className="flex gap-3 px-6 py-4 border-b border-gray-200 hover:bg-gray-50 cursor-pointer transition-colors"
              >
                <input
                  type="checkbox"
                  className="w-5 h-5 mt-0.5 rounded-full border-gray-300 text-purple-600 focus:ring-purple-500"
                  checked={!!selectedItems[it.zotero_key]}
                  onChange={() => toggleSelect(it.zotero_key)}
                />
                <div className="flex-1 min-w-0">
                  <div className="text-base font-semibold text-gray-900 mb-1">{it.title}</div>
                  <div className="text-sm text-gray-600 mb-1">{(it.authors || []).join(', ')}</div>
                  <div className="text-xs text-gray-500">{[it.year, it.item_type].filter(Boolean).join(' • ')}</div>
                </div>
              </label>
            ))}
          </div>

          <div className="border-t border-gray-200 px-6 py-4 bg-white flex justify-end">
            <Button
              className="rounded-full bg-gray-200 hover:bg-gray-300 text-black px-6 py-2 font-medium disabled:opacity-50 disabled:cursor-not-allowed shadow-sm"
              onClick={stageSelected}
              disabled={!selectedCollection || selectedCount === 0}
            >
              {selectedCount > 0 ? `Add selected (${selectedCount})` : 'Add selected'}
            </Button>
          </div>
        </div>

        <div className="w-[30%] flex flex-col bg-white">
          <div className="px-6 py-4 border-b border-gray-200">
            <div className="text-lg font-semibold">Selected</div>
          </div>

          <div className="flex-1 overflow-auto">
            {stagedCount === 0 && (
              <div className="px-6 py-8 text-center text-gray-500 text-sm">No papers selected yet</div>
            )}
            {(staged?.staged_items || []).map((it) => (
              <div
                key={it.zotero_key}
                className="px-6 py-4 border-b border-gray-200 hover:bg-gray-50 transition-colors group"
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex-1 min-w-0">
                    <div className="text-base font-semibold text-gray-900 mb-1">{it.title}</div>
                    <div className="text-sm text-gray-600 mb-1">{(it.authors || []).join(', ')}</div>
                    <div className="text-xs text-gray-500">{[it.year, it.item_type].filter(Boolean).join(' • ')}</div>
                  </div>
                  <button
                    className="text-gray-400 hover:text-red-600 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0"
                    onClick={() => removeStaged([it.zotero_key])}
                    aria-label="Remove"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>
              </div>
            ))}
          </div>

          <div className="border-t border-gray-200 px-6 py-4 bg-white flex justify-end">
            <Button
              className="rounded-full bg-purple-600 hover:bg-purple-700 text-white px-6 py-2 font-medium disabled:opacity-50 disabled:cursor-not-allowed"
              onClick={startMatch}
              disabled={stagedCount === 0}
            >
              Done selecting Seeds
            </Button>
          </div>
        </div>
      </div>

      {matchRes && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-3xl shadow-2xl max-w-4xl w-full max-h-[80vh] overflow-auto">
            <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex justify-between items-center rounded-t-3xl">
              <h2 className="text-xl font-bold">Unable to Match to API</h2>
              <button className="text-gray-400 hover:text-gray-600" onClick={() => setMatchRes(null)}>
                <X className="w-6 h-6" />
              </button>
            </div>

            <div className="p-6 space-y-0">
              {(matchRes.results || []).filter((r) => !r.matched).map((r, idx, arr) => (
                <div key={r.zotero_key} className={`py-4 bg-white ${idx !== arr.length - 1 ? 'border-b border-gray-200' : ''}`}>
                  <div className="font-semibold text-gray-900 mb-2">{r.title}</div>
                  {r.matched ? (
                    <div className="text-green-600 text-sm font-medium">
                      ✓ Matched: {r.paper_id} (Confidence: {Math.round((r.confidence || 0) * 100)}%)
                    </div>
                  ) : (
                    <div className="flex items-center justify-between">
                      {manualSelections[r.zotero_key] === undefined && (
                        <span className="text-yellow-700 text-sm font-medium">Needs review</span>
                      )}
                      {manualSelections[r.zotero_key] === '' && (
                        <span className="text-gray-600 text-sm font-medium">Skipped</span>
                      )}
                      {manualSelections[r.zotero_key] && (
                        <span className="text-green-700 text-sm font-medium truncate">Selected: {manualSelections[r.zotero_key]}</span>
                      )}
                      <Button
                        variant="outline"
                        size="sm"
                        className="rounded-full"
                        onClick={() => openReview(r)}
                      >
                        {manualSelections[r.zotero_key] === undefined ? 'Review candidates' : 'Change selection'}
                      </Button>
                    </div>
                  )}
                </div>
              ))}
            </div>

            <div className="sticky bottom-0 bg-white border-t border-gray-200 px-6 py-4 flex justify-end rounded-b-3xl">
              <Button
                className="rounded-full bg-purple-600 hover:bg-purple-700 text-white px-6 py-2"
                onClick={confirmMatches}
              >
                Confirm and add seeds
              </Button>
            </div>
          </div>
        </div>
      )}

      {reviewItem && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-3xl shadow-2xl max-w-2xl w-full max-h-[80vh] flex flex-col">
            <div className="border-b border-gray-200 px-6 py-4 flex justify-between items-start rounded-t-3xl">
              <div className="flex-1">
                <h3 className="text-xl font-bold mb-2">Paper not found in API</h3>
                <div className="text-sm text-gray-600">
                  Your paper: <span className="font-medium">{reviewItem.title}</span>
                </div>
              </div>
              <button className="text-gray-400 hover:text-gray-600 ml-4" onClick={closeReview}>
                <X className="w-6 h-6" />
              </button>
            </div>

            <div className="flex-1 overflow-auto p-6">
              {Array.isArray(reviewItem.candidates) && reviewItem.candidates.length > 0 ? (
                <div className="space-y-0">
                  {reviewItem.candidates.map((c, idx, arr) => {
                    const sel = manualSelections[reviewItem.zotero_key]
                    const isSelected = sel === c.paper_id
                    return (
                      <div key={c.paper_id} className={`py-4 bg-white ${idx !== arr.length - 1 ? 'border-b border-gray-200' : ''}`}>
                        <div className="font-semibold text-gray-900 mb-2">{c.title}</div>
                        <div className="text-sm text-gray-600 space-y-1 mb-3">
                          <div><span className="font-medium">Similarity:</span> {Math.round((c.similarity || 0) * 100)}%</div>
                          <div><span className="font-medium">PaperID:</span> {c.paper_id}</div>
                          {c.year && <div><span className="font-medium">Year:</span> {c.year}</div>}
                          {c.venue && <div><span className="font-medium">Venue:</span> {c.venue}</div>}
                          {c.doi && <div><span className="font-medium">DOI:</span> {c.doi}</div>}
                        </div>
                        <Button
                          className={`w-full rounded-full ${isSelected ? 'bg-green-600 hover:bg-green-700 text-white' : 'bg-gray-900 hover:bg-gray-800 text-white'}`}
                          onClick={() => chooseCandidate(reviewItem.zotero_key, c.paper_id)}
                        >
                          {isSelected ? 'Selected' : 'Use as Seed'}
                        </Button>
                      </div>
                    )
                  })}
                </div>
              ) : (
                <div className="text-center text-gray-500 py-8">
                  No candidates available for this item.
                </div>
              )}
            </div>

            <div className="border-t border-gray-200 px-6 py-4 flex justify-end rounded-b-3xl">
              <Button
                variant="outline"
                className="rounded-full"
                onClick={() => skipCandidate(reviewItem.zotero_key)}
              >
                Skip Seed
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
