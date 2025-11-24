import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import Stepper from '@/components/Stepper'
import apiClient from '@/shared/api/client'
import { endpoints } from '@/shared/api/endpoints'
import { getSessionId, hydrateSessionFromQuery } from '@/shared/lib/session'

export default function PdfImportPage() {
  const steps = ['Seed papers', 'Library details', 'Review & Create']
  const [sessionId, setSessionId] = useState(null)
  const [files, setFiles] = useState([])
  const [uploadRes, setUploadRes] = useState(null)
  const [extractRes, setExtractRes] = useState(null)
  const [reviews, setReviews] = useState({})
  const [editingPaper, setEditingPaper] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const navigate = useNavigate()

  useEffect(() => {
    const sid = getSessionId() || hydrateSessionFromQuery()
    if (!sid) { navigate('/'); return }
    setSessionId(sid)
  }, [navigate])

  const onSelectFiles = async (e) => {
    const list = Array.from(e.target.files || [])
    setFiles(list)
    if (list.length > 0) {
      await upload(list)
    }
  }

  const onDrop = async (e) => {
    e.preventDefault()
    const list = Array.from(e.dataTransfer.files || []).filter(f => f.type === 'application/pdf')
    setFiles(list)
    if (list.length > 0) {
      await upload(list)
    }
  }

  const onDragOver = (e) => {
    e.preventDefault()
  }

  const upload = async (fileList = files) => {
    if (!sessionId || !fileList.length) return
    setLoading(true)
    setError(null)
    const fd = new FormData()

    fileList.forEach((f) => {
      fd.append('files', f, f.name)
    })
    const res = await apiClient('POST', `${endpoints.seedsSession}/${sessionId}/pdfs/upload`, fd)
    if (res.error) setError(res.error)
    else setUploadRes(res.data)
    setLoading(false)
  }

  const processPdfs = async () => {
    if (!sessionId || !uploadRes?.upload_id) return
    setLoading(true)
    setError(null)
    const res = await apiClient('POST', `${endpoints.seedsSession}/${sessionId}/pdfs/${uploadRes.upload_id}/extract`)
    if (res.error) setError(res.error)
    else {
      setExtractRes(res.data)
      const next = {}
      ;(res.data?.results || []).forEach((r) => {
        next[r.filename] = { action: r.success ? 'accept' : 'skip', edited_metadata: r.metadata || null }
      })
      setReviews(next)
    }
    setLoading(false)
  }

  const openEdit = (result) => {
    const rv = reviews[result.filename] || { action: 'accept', edited_metadata: result.metadata || {} }
    setEditingPaper({ ...result, review: rv })
  }

  const closeEdit = () => {
    setEditingPaper(null)
  }

  const saveEdit = () => {
    if (!editingPaper) return
    setReviews((prev) => ({
      ...prev,
      [editingPaper.filename]: { ...(editingPaper.review || {}), action: 'edit' }
    }))
    closeEdit()
  }

  const updateEditField = (field, value) => {
    setEditingPaper((prev) => ({
      ...prev,
      review: {
        ...(prev.review || {}),
        action: 'edit',
        edited_metadata: {
          ...((prev.review && prev.review.edited_metadata) || {}),
          [field]: value
        }
      }
    }))
  }

  const skipPaper = (filename) => {
    setReviews((prev) => ({
      ...prev,
      [filename]: { ...(prev[filename] || {}), action: 'skip' }
    }))
  }

  const useAsSeeds = async () => {
    if (!sessionId || !uploadRes?.upload_id) return
    setLoading(true)
    setError(null)
    const reviewPayload = {
      reviews: Object.entries(reviews).map(([filename, r]) => ({ filename, action: r.action, edited_metadata: r.edited_metadata })),
    }
    const rv = await apiClient(
      'POST',
      `${endpoints.seedsSession}/${sessionId}/pdfs/${uploadRes.upload_id}/review`,
      reviewPayload
    )
    if (rv.error) {
      setError(rv.error)
      setLoading(false)
      return
    }
    const fd = new FormData()
    fd.append('api_provider', 'openalex')
    const match = await apiClient(
      'POST',
      `${endpoints.seedsSession}/${sessionId}/pdfs/${uploadRes.upload_id}/match`,
      fd
    )
    if (match.error) {
      setError(match.error)
      setLoading(false)
      return
    }
    const cf = await apiClient(
      'POST',
      `${endpoints.seedsSession}/${sessionId}/pdfs/${uploadRes.upload_id}/confirm`,
      { action: 'use_all' }
    )
    if (cf.error) setError(cf.error)
    else navigate('/create/staging')
    setLoading(false)
  }

  const acceptedPapers = extractRes?.results?.filter(r => reviews[r.filename]?.action !== 'skip') || []
  const displayedPapers = extractRes?.results?.filter(r => reviews[r.filename]?.action !== 'skip') || []

  return (
    <div className="min-h-screen bg-white">
      {error && (
        <div className="bg-red-50 border-b border-red-200 px-6 py-3 text-red-700 text-sm">
          Error: {error}
        </div>
      )}

      <div className="pt-8">
        <Stepper currentStep={1} steps={steps} />
      </div>

      <div className="max-w-7xl mx-auto px-8 py-8">
        <h1 className="text-3xl font-bold mb-8">Extract papers from PDFs</h1>

        <div className="grid grid-cols-1 lg:grid-cols-[400px_1fr] gap-6">
          <div className="border border-gray-300 rounded-3xl p-6 flex flex-col h-[600px]">
            <h2 className="text-lg font-semibold mb-4">Select source</h2>
            
            <div
              className="flex-1 border-2 border-dashed border-gray-300 rounded-2xl flex flex-col items-center justify-center mb-4"
              onDrop={onDrop}
              onDragOver={onDragOver}
            >
              <svg className="w-16 h-16 text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <p className="text-gray-700 font-medium mb-1">Drop PDF files here</p>
              <p className="text-gray-400 text-sm">Supports multiple pdf files</p>
            </div>

            <div className="flex gap-3 mb-4">
              <label className="flex-1">
                <input
                  type="file"
                  multiple
                  accept="application/pdf"
                  onChange={onSelectFiles}
                  className="hidden"
                />
                <div className="w-full px-4 py-2 rounded-full border border-gray-300 bg-white text-center cursor-pointer hover:bg-gray-50 transition-colors text-sm font-medium">
                  Select files
                </div>
              </label>
              <label className="flex-1">
                <input
                  type="file"
                  webkitdirectory="true"
                  directory="true"
                  onChange={onSelectFiles}
                  className="hidden"
                />
                <div className="w-full px-4 py-2 rounded-full border border-gray-300 bg-white text-center cursor-pointer hover:bg-gray-50 transition-colors text-sm font-medium">
                  Select folder
                </div>
              </label>
            </div>

            {files.length > 0 && (
              <div className="text-sm text-gray-700 mb-4">
                {files.length} PDF{files.length !== 1 ? 's' : ''} loaded
              </div>
            )}

            <div className="mt-auto">
              <Button
                className="w-full rounded-full bg-gray-600 hover:bg-gray-700 text-white font-medium"
                onClick={processPdfs}
                disabled={!uploadRes?.upload_id || loading}
              >
                Process PDFs
              </Button>
            </div>
          </div>

          <div className="border border-gray-300 rounded-3xl p-6 flex flex-col h-[600px]">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold">Extracted papers</h2>
              {acceptedPapers.length > 0 && (
                <span className="px-3 py-1 rounded-full bg-purple-600 text-white text-xs font-medium">
                  {acceptedPapers.length} paper{acceptedPapers.length !== 1 ? 's' : ''}
                </span>
              )}
            </div>

            <div className="flex-1 overflow-auto -mx-6">
              {!extractRes && (
                <div className="px-6 py-8 text-center text-gray-500 text-sm">
                  No papers extracted yet
                </div>
              )}
              {extractRes && displayedPapers.length === 0 && (
                <div className="px-6 py-8 text-center text-gray-500 text-sm">
                  All papers skipped
                </div>
              )}
              {displayedPapers.map((result, idx) => {
                  const rv = reviews[result.filename] || { action: 'accept', edited_metadata: result.metadata || {} }
                  const metadata = rv.edited_metadata || result.metadata || {}
                  return (
                  <div
                    key={result.filename}
                    className={`px-6 py-4 ${idx !== displayedPapers.length - 1 ? 'border-b border-gray-200' : ''}`}
                  >
                    <h3 className="font-semibold text-gray-900 mb-2">
                      {metadata.title || result.filename}
                    </h3>
                    <div className="flex items-start gap-4">
                      <div className="flex-1 text-sm text-gray-600 space-y-1">
                        {metadata.authors && (
                          <div><span className="font-medium">Authors:</span> {metadata.authors}</div>
                        )}
                        {metadata.venue && (
                          <div><span className="font-medium">Venue:</span> {metadata.venue}</div>
                        )}
                        {metadata.year && (
                          <div><span className="font-medium">Year:</span> {metadata.year}</div>
                        )}
                        {metadata.doi && (
                          <div><span className="font-medium">DOI:</span> {metadata.doi}</div>
                        )}
                        {!metadata.venue && !metadata.year && !metadata.doi && (
                          <>
                            <div><span className="font-medium">Venue:</span> Not found</div>
                            <div><span className="font-medium">Year:</span> Not found</div>
                            <div><span className="font-medium">DOI:</span> Not found</div>
                          </>
                        )}
                      </div>
                      <div className="flex gap-2 flex-shrink-0">
                        <Button
                          variant="outline"
                          size="sm"
                          className="rounded-full"
                          onClick={() => openEdit(result)}
                        >
                          Edit
                        </Button>
                        <Button
                          size="sm"
                          className="rounded-full bg-purple-600 hover:bg-purple-700 text-white"
                          onClick={() => skipPaper(result.filename)}
                        >
                          Skip
                        </Button>
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>

            {extractRes && acceptedPapers.length > 0 && (
              <div className="mt-4 pt-4 border-t border-gray-200">
                <Button
                  className="w-full rounded-full bg-gray-900 hover:bg-gray-800 text-white font-medium"
                  onClick={useAsSeeds}
                  disabled={loading}
                >
                  Use as seed papers
                </Button>
              </div>
            )}
          </div>
        </div>
      </div>

      {editingPaper && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-3xl shadow-2xl max-w-lg w-full">
            <div className="border-b border-gray-200 px-6 py-4 flex justify-between items-center rounded-t-3xl">
              <h3 className="text-xl font-bold">Edit this paper's metadata</h3>
              <button className="text-gray-400 hover:text-gray-600" onClick={closeEdit}>
                <X className="w-6 h-6" />
              </button>
            </div>

            <div className="p-6 space-y-4">
              <div>
                <Label htmlFor="edit-title" className="text-sm font-medium text-gray-700 mb-1 block">
                  Title
                </Label>
                <Input
                  id="edit-title"
                  className="w-full"
                  value={editingPaper.review.edited_metadata?.title || ''}
                  onChange={(e) => updateEditField('title', e.target.value)}
                />
              </div>

              <div>
                <Label htmlFor="edit-authors" className="text-sm font-medium text-gray-700 mb-1 block">
                  Authors
                </Label>
                <Input
                  id="edit-authors"
                  className="w-full"
                  value={editingPaper.review.edited_metadata?.authors || ''}
                  onChange={(e) => updateEditField('authors', e.target.value)}
                />
              </div>

              <div>
                <Label htmlFor="edit-venue" className="text-sm font-medium text-gray-700 mb-1 block">
                  Venue
                </Label>
                <Input
                  id="edit-venue"
                  className="w-full"
                  value={editingPaper.review.edited_metadata?.venue || ''}
                  onChange={(e) => updateEditField('venue', e.target.value)}
                />
              </div>

              <div>
                <Label htmlFor="edit-year" className="text-sm font-medium text-gray-700 mb-1 block">
                  Year
                </Label>
                <Input
                  id="edit-year"
                  className="w-full"
                  value={editingPaper.review.edited_metadata?.year || ''}
                  onChange={(e) => updateEditField('year', e.target.value)}
                />
              </div>

              <div>
                <Label htmlFor="edit-doi" className="text-sm font-medium text-gray-700 mb-1 block">
                  DOI
                </Label>
                <Input
                  id="edit-doi"
                  className="w-full"
                  value={editingPaper.review.edited_metadata?.doi || ''}
                  onChange={(e) => updateEditField('doi', e.target.value)}
                />
              </div>
            </div>

            <div className="border-t border-gray-200 px-6 py-4 flex justify-end rounded-b-3xl">
              <Button
                className="rounded-full bg-gray-900 hover:bg-gray-800 text-white px-6"
                onClick={saveEdit}
              >
                Accept
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
