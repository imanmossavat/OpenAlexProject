import { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { AlertCircle, ArrowLeft, CheckCircle2, ExternalLink } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import apiClient from '@/shared/api/client'
import { endpoints } from '@/shared/api/endpoints'
import { getSessionId, hydrateSessionFromQuery } from '@/shared/lib/session'
import PaperDetailModal from '@/components/PaperDetailModal'
import Stepper from '@/components/Stepper'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'

export default function MatchedSeedsPage() {
  const navigate = useNavigate()
  const [sessionId, setSessionId] = useState(null)
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [selected, setSelected] = useState({})
  const [confirming, setConfirming] = useState(false)
  const [selectedPaper, setSelectedPaper] = useState(null)
  const [page, setPage] = useState(1)
  const pageSize = 10
  const [editingRow, setEditingRow] = useState(null)
  const [editFields, setEditFields] = useState({})
  const [editError, setEditError] = useState(null)
  const [savingEdit, setSavingEdit] = useState(false)

  useEffect(() => {
    const sid = getSessionId() || hydrateSessionFromQuery()
    if (!sid) {
      navigate('/')
      return
    }
    setSessionId(sid)
  }, [navigate])

  const loadMatches = useCallback(async () => {
    if (!sessionId) return
    setLoading(true)
    setError(null)
    const res = await apiClient('GET', `${endpoints.seedsSession}/${sessionId}/staging/match`)
    if (res.error) {
      setError(res.error)
    } else {
      setData(res.data || null)
      const initial = {}
      ;(res.data?.matched_rows || []).forEach((row) => {
        initial[row.staging_id] = true
      })
      setSelected(initial)
      setPage(1)
    }
    setLoading(false)
  }, [sessionId])

  useEffect(() => {
    loadMatches()
  }, [loadMatches])

  const matchedRows = data?.matched_rows || []
  const unmatchedRows = data?.unmatched_rows || []
  const totalPages = Math.max(1, Math.ceil(matchedRows.length / pageSize))
  const pagedMatchedRows = matchedRows.slice((page - 1) * pageSize, page * pageSize)

  const toggleRow = (stagingId) => {
    setSelected((prev) => ({ ...prev, [stagingId]: !prev[stagingId] }))
  }

  const confirmMatches = async () => {
    const stagingIds = matchedRows.filter((row) => selected[row.staging_id]).map((row) => row.staging_id)
    if (!stagingIds.length) {
      setError('Select at least one matched paper to continue.')
      return
    }
    setConfirming(true)
    const res = await apiClient('POST', `${endpoints.seedsSession}/${sessionId}/staging/match/confirm`, {
      staging_ids: stagingIds,
    })
    setConfirming(false)
    if (res.error) {
      setError(res.error)
    } else {
      navigate('/create/details')
    }
  }


  const openEditModal = (row) => {
    const staging = row.staging || {}
    setEditingRow(row)
    setEditFields({
      title: staging.title || '',
      authors: staging.authors || '',
      year: staging.year || '',
      venue: staging.venue || '',
      doi: staging.doi || '',
      url: staging.url || '',
    })
    setEditError(null)
  }

  const handleEditField = (field, value) => {
    setEditFields((prev) => ({ ...prev, [field]: value }))
  }

  const saveEdit = async () => {
    if (!editingRow) return
    setSavingEdit(true)
    setEditError(null)
    const payload = {
      title: editFields.title || null,
      authors: editFields.authors || null,
      year: editFields.year ? Number(editFields.year) : null,
      venue: editFields.venue || null,
      doi: editFields.doi || null,
      url: editFields.url || null,
    }
    try {
      const patchRes = await apiClient(
        'PATCH',
        `${endpoints.seedsSession}/${sessionId}/staging/${editingRow.staging_id}`,
        payload
      )
      if (patchRes.error) throw new Error(patchRes.error)
      const rematchRes = await apiClient(
        'POST',
        `${endpoints.seedsSession}/${sessionId}/staging/${editingRow.staging_id}/rematch`,
        { api_provider: 'openalex' }
      )
      if (rematchRes.error) throw new Error(rematchRes.error)
      await loadMatches()
      setEditingRow(null)
    } catch (err) {
      setEditError(err.message || 'Failed to update paper.')
    }
    setSavingEdit(false)
  }

  return (
    <div className="min-h-[calc(100vh-160px)] bg-white">
      <div className="max-w-5xl mx-auto px-6 py-10">
        <div className="mb-6">
          <Stepper currentStep={3} steps={['Add', 'Stage', 'Match', 'Library']} />
        </div>
        <div className="flex items-center gap-4 mb-8">
          <Button
            variant="outline"
            className="rounded-full"
            onClick={() => navigate('/create/staging')}
          >
            <ArrowLeft className="w-4 h-4 mr-2" /> Back to staging
          </Button>
          <div>
            <p className="text-xs uppercase tracking-[0.3em] text-gray-500 mb-1">Matching</p>
            <h1 className="text-3xl font-semibold text-gray-900">Review matched seed papers</h1>
          </div>
        </div>

        {error && (
          <div className="mb-6 rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 flex items-center gap-2">
            <AlertCircle className="w-4 h-4" />
            {error}
          </div>
        )}

        {loading ? (
          <div className="text-gray-500">Loading match results...</div>
        ) : !data ? (
          <div className="text-gray-500">No match results available. Run matching from the staging page.</div>
        ) : (
          <>
            <section className="mb-10">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h2 className="text-xl font-semibold text-gray-900">Matches ready to add</h2>
                  <p className="text-sm text-gray-500">
                    {matchedRows.length
                      ? 'Select the papers you want to finalize before continuing.'
                      : 'No automatic matches were found.'}
                  </p>
                </div>
                {matchedRows.length > 0 && (
                  <div className="text-sm text-gray-500">
                    {Object.values(selected).filter(Boolean).length} of {matchedRows.length} selected
                  </div>
                )}
              </div>

              {matchedRows.length === 0 ? (
                <div className="rounded-2xl border border-gray-200 bg-gray-50 px-5 py-4 text-sm text-gray-600">
                  None of the selected papers could be matched. Adjust metadata and try again.
                </div>
              ) : (
                <div className="space-y-0">
                  {pagedMatchedRows.map((row, idx) => (
                    <MatchedRowCard
                      key={row.staging_id}
                      row={row}
                      index={(page - 1) * pageSize + idx}
                      checked={!!selected[row.staging_id]}
                      onToggle={() => toggleRow(row.staging_id)}
                      onViewDetails={(paper) => setSelectedPaper(paper)}
                    />
                  ))}
                  {totalPages > 1 && (
                    <div className="flex items-center justify-between px-4 py-3 text-xs text-gray-500 border-t border-gray-100">
                      <span>
                        Showing {(page - 1) * pageSize + 1}–
                        {Math.min(page * pageSize, matchedRows.length)} of {matchedRows.length} matches
                      </span>
                      <div className="flex items-center gap-2">
                        <button
                          type="button"
                          className="px-3 py-1 rounded-full border border-gray-200 hover:border-gray-300 disabled:opacity-40"
                          disabled={page <= 1}
                          onClick={() => setPage((prev) => Math.max(1, prev - 1))}
                        >
                          Previous
                        </button>
                        <button
                          type="button"
                          className="px-3 py-1 rounded-full border border-gray-200 hover:border-gray-300 disabled:opacity-40"
                          disabled={page >= totalPages}
                          onClick={() => setPage((prev) => Math.min(totalPages, prev + 1))}
                        >
                          Next
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </section>

            <section className="mb-12">
              <h2 className="text-xl font-semibold text-gray-900 mb-3">Unmatched papers</h2>
              {unmatchedRows.length === 0 ? (
                <div className="text-sm text-gray-500">All selected papers matched successfully.</div>
              ) : (
                <div className="space-y-0">
                  {unmatchedRows.map((row, idx) => (
                    <UnmatchedRowCard key={row.staging_id} row={row} index={idx} onEdit={() => openEditModal(row)} />
                  ))}
                </div>
              )}
            </section>

            <div className="flex items-center justify-between border-t border-gray-200 pt-6">
              <div className="text-sm text-gray-500">
                Forgot to addd papers? You can still go back to select more papers.
              </div>
              <Button
                className="rounded-full bg-gray-900 text-white hover:bg-gray-800 disabled:opacity-60"
                onClick={confirmMatches}
                disabled={!matchedRows.length || confirming}
              >
                {confirming ? 'Saving...' : 'Confirm & continue'}
              </Button>
            </div>
          </>
        )}
      </div>

      <PaperDetailModal paper={selectedPaper} isOpen={!!selectedPaper} onClose={() => setSelectedPaper(null)} />

      <Dialog open={!!editingRow} onOpenChange={(open) => !open && !savingEdit && setEditingRow(null)}>
        <DialogContent className="sm:max-w-lg bg-white rounded-3xl border-0">
          <DialogHeader>
            <DialogTitle>Edit metadata & retry match</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label className="text-xs uppercase text-gray-500">Title</Label>
              <Input value={editFields.title || ''} onChange={(e) => handleEditField('title', e.target.value)} />
            </div>
            <div>
              <Label className="text-xs uppercase text-gray-500">Authors</Label>
              <Input value={editFields.authors || ''} onChange={(e) => handleEditField('authors', e.target.value)} />
            </div>
            <div className="flex gap-3">
              <div className="flex-1">
                <Label className="text-xs uppercase text-gray-500">Year</Label>
                <Input
                  type="number"
                  value={editFields.year || ''}
                  onChange={(e) => handleEditField('year', e.target.value)}
                />
              </div>
              <div className="flex-1">
                <Label className="text-xs uppercase text-gray-500">Venue</Label>
                <Input value={editFields.venue || ''} onChange={(e) => handleEditField('venue', e.target.value)} />
              </div>
            </div>
            <div className="flex gap-3">
              <div className="flex-1">
                <Label className="text-xs uppercase text-gray-500">DOI</Label>
                <Input value={editFields.doi || ''} onChange={(e) => handleEditField('doi', e.target.value)} />
              </div>
              <div className="flex-1">
                <Label className="text-xs uppercase text-gray-500">URL</Label>
                <Input value={editFields.url || ''} onChange={(e) => handleEditField('url', e.target.value)} />
              </div>
            </div>
            {editError && <div className="text-sm text-red-600">{editError}</div>}
          </div>
          <div className="flex justify-end gap-2 pt-4">
            <Button variant="outline" className="rounded-full" onClick={() => setEditingRow(null)} disabled={savingEdit}>
              Cancel
            </Button>
            <Button className="rounded-full bg-gray-900 text-white" onClick={saveEdit} disabled={savingEdit}>
              {savingEdit ? 'Saving…' : 'Save & retry'}
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  )
}

function MatchedRowCard({ row, index, checked, onToggle, onViewDetails }) {
  const staging = row.staging || {}
  const match = row.matched_seed || {}
  
  const authors = Array.isArray(match.authors) ? match.authors.join(', ') : (match.authors || 'Unknown authors')
  const year = match.year || ''
  const citations = (typeof match.cited_by_count === 'number') ? String(match.cited_by_count) + ' Citations' : ''
  const references = (typeof match.references_count === 'number') ? String(match.references_count) + ' references' : ''
  const meta = [year, citations, references].filter(Boolean).join(' • ')

  const openAlexUrl = typeof match.paper_id === 'string' && /^[Ww]/.test(match.paper_id)
    ? `https://openalex.org/${match.paper_id}`
    : null

  return (
    <div 
      className={`bg-white border-b border-gray-200 p-6 hover:bg-gray-50 transition-colors duration-200 cursor-pointer ${
        checked ? 'bg-gray-50' : ''
      }`}
      onClick={(e) => {
        if (e.target.tagName !== 'INPUT' && e.target.tagName !== 'BUTTON' && !e.target.closest('button')) {
          onViewDetails(match)
        }
      }}
    >
      <div className="flex items-start gap-4">
        <input
          type="checkbox"
          className="mt-2 rounded border-gray-300 text-gray-900 focus:ring-gray-900"
          checked={checked}
          onChange={onToggle}
          onClick={(e) => e.stopPropagation()}
        />

        <div className="w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center flex-shrink-0">
          <span className="text-sm font-semibold text-gray-700">{index + 1}</span>
        </div>
        
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-2">
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-purple-100 text-purple-700 text-[10px] font-semibold uppercase tracking-wider">
              <CheckCircle2 className="w-3 h-3" /> {row.match_method || 'Match'}
            </span>
            {typeof row.confidence === 'number' && (
              <span className="text-xs text-gray-500">{Math.round(row.confidence * 100)}% confident</span>
            )}
          </div>

          <div className="text-lg font-semibold text-gray-900 mb-2">
            {match.title || match.paper_id}
          </div>
          
          {match.abstract && (
            <div className="text-sm text-gray-600 mb-3 line-clamp-2 max-h-16 overflow-hidden">
              {match.abstract}
            </div>
          )}
          
          {authors && (
            <div className="text-sm text-gray-500 mb-2">{authors}</div>
          )}
          
          {meta && (
            <div className="text-xs text-gray-500">{meta}</div>
          )}
        </div>
        
        <div className="flex gap-2 flex-shrink-0">
          {openAlexUrl && (
            <Button
              variant="outline"
              size="sm"
              className="bg-gray-100 hover:bg-gray-200 border-gray-300"
              onClick={(e) => { e.stopPropagation(); window.open(openAlexUrl, '_blank') }}
            >
              OpenAlex <ExternalLink className="w-4 h-4 ml-1" />
            </Button>
          )}
        </div>
      </div>
    </div>
  )
}

function UnmatchedRowCard({ row, index, onEdit }) {
  const staging = row.staging || {}
  
  return (
    <div className="bg-white border-b border-gray-200 p-6 hover:bg-gray-50 transition-colors duration-200">
      <div className="flex items-start gap-4">
        <div className="w-8 h-8 rounded-full bg-red-100 flex items-center justify-center flex-shrink-0">
          <span className="text-sm font-semibold text-red-700">{index + 1}</span>
        </div>
        
        <div className="flex-1 min-w-0">
          <div className="text-lg font-semibold text-gray-900 mb-2">
            {staging.title || 'Untitled paper'}
          </div>
          
          <div className="text-sm text-gray-500 mb-2">
            {staging.authors || 'Unknown authors'} • {staging.year || 'Year n/a'}
          </div>
          
          <div className="text-xs text-red-600 mt-2 flex items-center gap-1">
            <AlertCircle className="w-3 h-3" />
            {row.error || 'No match found with the provided metadata.'}
          </div>
          <div className="mt-3">
            <Button variant="outline" size="sm" className="rounded-full" onClick={onEdit}>
              Edit & retry
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}
