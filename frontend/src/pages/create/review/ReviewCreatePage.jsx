import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import Stepper from '@/components/Stepper'
import apiClient from '@/shared/api/client'
import { endpoints } from '@/shared/api/endpoints'
import { getSessionId, hydrateSessionFromQuery, clearSession } from '@/shared/lib/session'

export default function ReviewCreatePage() {
  const navigate = useNavigate()
  const steps = ['Add', 'Stage', 'Match', 'Library']
  const [sessionId, setSessionId] = useState(null)
  const [preview, setPreview] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [creating, setCreating] = useState(false)

  useEffect(() => {
    const sid = getSessionId() || hydrateSessionFromQuery()
    if (!sid) { navigate('/'); return }
    setSessionId(sid)
  }, [navigate])

  useEffect(() => {
    if (!sessionId) return
    ;(async () => {
      const pv = await apiClient('GET', `${endpoints.library}/${sessionId}/preview`)
      if (pv.error) setError(pv.error)
      else setPreview(pv.data)
      setLoading(false)
    })()
  }, [sessionId])

  const createLibrary = async () => {
    if (!sessionId) return
    setCreating(true)
    setError(null)
    const res = await apiClient('POST', `${endpoints.library}/${sessionId}/create`)
    if (res.error) {
      setError(res.error)
      setCreating(false)
    } else {
      clearSession()
      navigate('/')
    }
  }

  return (
    <div className="w-full flex flex-col bg-white">
      <div className="pt-8">
        <Stepper currentStep={4} steps={steps} />
      </div>

      <div className="px-6 py-6 pb-24">
        <div className="w-full max-w-6xl mx-auto">
          <h1 className="text-3xl font-bold mb-8">Library Creation - Step 3: Review & Create</h1>

          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
              {error}
            </div>
          )}

          {loading ? (
            <div className="text-gray-500">Loading preview...</div>
          ) : (
            <div className="bg-white rounded-2xl border border-gray-200 shadow-sm">
              <div className="px-8 py-6 border-b border-gray-200">
                <h2 className="text-xl font-semibold">Review Configuration</h2>
              </div>

              <div className="px-8 py-6">
                <h3 className="text-base font-semibold mb-6">Configuration Summary</h3>
                
                <div className="grid grid-cols-2 gap-x-16 gap-y-6">
                  <div>
                    <div className="mb-4">
                      <div className="text-sm text-gray-600 mb-1">Name:</div>
                      <div className="text-base font-medium">{preview?.name || 'N/A'}</div>
                    </div>
                    <div className="mb-4">
                      <div className="text-sm text-gray-600 mb-1">Location:</div>
                      <div className="text-base font-medium">{preview?.path || 'Default location'}</div>
                    </div>
                    <div>
                      <div className="text-sm text-gray-600 mb-1">Description:</div>
                      <div className="text-base font-medium">
                        {preview?.description || 'No description provided'}
                      </div>
                    </div>
                  </div>

                  <div>
                    <div className="mb-4">
                      <div className="text-sm text-gray-600 mb-1">Papers:</div>
                      <div className="text-base font-medium">
                        {preview?.total_papers || 0} papers selected
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="border-t border-gray-200 px-6 py-4 bg-white">
        <div className="max-w-6xl mx-auto flex justify-between">
          <Button
            variant="outline"
            className="px-6 py-2 rounded-full border-gray-300 shadow-md hover:shadow-lg transition-all duration-200"
            onClick={() => navigate('/create/details')}
            disabled={creating}
          >
            Back
          </Button>
          <Button
            className="px-6 py-2 rounded-full bg-gray-900 text-white hover:bg-gray-800 shadow-md hover:shadow-lg transition-all duration-200 disabled:opacity-50"
            onClick={createLibrary}
            disabled={creating || loading}
          >
            {creating ? 'Creating...' : 'Create Library'}
          </Button>
        </div>
      </div>
    </div>
  )
}
