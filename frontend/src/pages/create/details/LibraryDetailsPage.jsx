import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import Stepper from '@/components/Stepper'
import apiClient from '@/shared/api/client'
import { endpoints } from '@/shared/api/endpoints'
import { getSessionId, getSessionUseCase, hydrateSessionFromQuery } from '@/shared/lib/session'

export default function LibraryDetailsPage() {
  const navigate = useNavigate()
  const steps = ['Add', 'Stage', 'Match', 'Library']
  const [sessionId, setSessionId] = useState(null)
  const [form, setForm] = useState({ name: '', path: '', description: '' })
  const [seedCount, setSeedCount] = useState(0)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [sessionUseCase] = useState(() => getSessionUseCase())

  useEffect(() => {
    const sid = getSessionId() || hydrateSessionFromQuery()
    if (!sid) { navigate('/'); return }
    setSessionId(sid)
    
    ;(async () => {
      const res = await apiClient('GET', `${endpoints.seedsSession}/${sid}`)
      if (!res.error && res.data) {
        setSeedCount(res.data.total_seeds ?? res.data.seeds?.length ?? 0)
      }
    })()
  }, [navigate])

  useEffect(() => {
    if (sessionUseCase === 'library_edit') {
      navigate('/create/review', { replace: true })
    }
  }, [sessionUseCase, navigate])

  const handleContinue = async () => {
    if (!sessionId || !form.name.trim()) {
      setError('Library name is required')
      return
    }

    setLoading(true)
    setError(null)

    const payload = { name: form.name.trim() }
    const trimmedPath = (form.path || '').trim()
    const trimmedDesc = (form.description || '').trim()
    if (trimmedPath) payload.path = trimmedPath
    if (trimmedDesc) payload.description = trimmedDesc

    const res = await apiClient('POST', `${endpoints.library}/${sessionId}/details`, payload)
    
    setLoading(false)

    if (res.error) {
      setError(res.error)
      return
    }

    navigate('/create/review')
  }

  const charCount = form.description.length
  const maxChars = 500

  const generateLocationPlaceholder = () => {
    const slugifiedName = form.name.trim().toLowerCase().replace(/\s+/g, '-') || 'my-research-library'
    return `/libraries/${slugifiedName}/`
  }

  return (
    <div className="w-full min-h-screen flex flex-col bg-white">
      <div className="pt-8">
        <Stepper currentStep={4} steps={steps} />
      </div>

      <div className="flex-1 flex items-center justify-center px-6 py-12">
        <div className="w-full max-w-6xl">
          <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-10">
            <h1 className="text-3xl font-bold mb-8">Library Details</h1>

            {error && (
              <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
                {error}
              </div>
            )}

            <div className="space-y-6">
              <div>
                <Label htmlFor="library-name" className="text-base font-semibold mb-2 block">
                  Library Name
                </Label>
                <Input
                  id="library-name"
                  type="text"
                  placeholder="My Research Library"
                  value={form.name}
                  onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
                  className="w-full px-4 py-3 border-2 border-gray-300 rounded-xl shadow-md hover:shadow-lg focus:outline-none focus:ring-0 focus:border-blue-500 transition-all duration-200"
                />
              </div>

              <div>
                <Label htmlFor="location" className="text-base font-semibold mb-2 block">
                  Location
                </Label>
                <Input
                  id="location"
                  type="text"
                  placeholder={generateLocationPlaceholder()}
                  value={form.path}
                  onChange={(e) => setForm((f) => ({ ...f, path: e.target.value }))}
                  className="w-full px-4 py-3 border-2 border-gray-300 rounded-xl shadow-md hover:shadow-lg focus:outline-none focus:ring-0 focus:border-blue-500 transition-all duration-200 placeholder:text-gray-400"
                />
                <p className="text-xs text-gray-500 mt-2">
                  Only change if you don't want to use the default path to save your library
                </p>
              </div>

              <div>
                <Label htmlFor="description" className="text-base font-semibold mb-2 block">
                  Description <span className="text-gray-500 font-normal">(Optional)</span>
                </Label>
                <textarea
                  id="description"
                  placeholder="A collection of papers on deep learning and computer vision for my research project."
                  value={form.description}
                  onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
                  maxLength={maxChars}
                  className="w-full min-h-[120px] px-4 py-3 border-2 border-gray-300 rounded-xl shadow-md hover:shadow-lg focus:outline-none focus:ring-0 focus:border-blue-500 resize-none transition-all duration-200"
                />
                <div className="flex justify-end mt-1">
                  <span className="text-xs text-gray-500">{charCount} / {maxChars}</span>
                </div>
              </div>

              <div className="flex items-start gap-3 p-4 bg-blue-50 border border-blue-200 rounded-xl">
                <div className="w-5 h-5 rounded-full bg-blue-500 text-white flex items-center justify-center flex-shrink-0 mt-0.5">
                  <span className="text-xs font-bold">i</span>
                </div>
                <p className="text-sm text-gray-700">
                  The library will be created with {seedCount} selected paper{seedCount !== 1 ? 's' : ''}.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

\      <div className="border-t border-gray-200 px-6 py-4 bg-white">
        <div className="max-w-6xl mx-auto flex justify-between">
          <Button
            variant="outline"
            className="px-6 py-2 rounded-full border-gray-300 shadow-md hover:shadow-lg transition-all duration-200"
            onClick={() => navigate('/create/staging/matched')}
          >
            Back
          </Button>
          <Button
            className="px-6 py-2 rounded-full bg-gray-900 text-white hover:bg-gray-800 shadow-md hover:shadow-lg transition-all duration-200 disabled:opacity-50"
            onClick={handleContinue}
            disabled={loading || !form.name.trim()}
          >
            {loading ? 'Saving...' : 'Continue'}
          </Button>
        </div>
      </div>
    </div>
  )
}
