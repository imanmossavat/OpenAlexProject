import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import apiClient from '@/shared/api/client'
import { endpoints } from '@/shared/api/endpoints'
import { getSessionId, setSessionId } from '@/shared/lib/session'
import { Button } from '@/components/ui/button'

export default function HomePage() {
  const [error, setError] = useState(null)
  const navigate = useNavigate()

  const handleCreateLibrary = async () => {
    const existing = getSessionId()
    if (existing) {
      navigate('/create/library-start')
      return
    }
    const res = await apiClient('POST', `${endpoints.seedsSession}/start`, { use_case: 'library_creation' })
    if (res.error) {
      setError(res.error)
      return
    }
    const sid = res.data?.session_id
    if (sid) setSessionId(sid, { useCase: 'library_creation' })
    navigate('/create/library-start')
  }

  return (
    <div className="min-h-[calc(100vh-160px)] bg-white flex items-center">
      <div className="w-full max-w-5xl mx-auto px-6 py-16">
        <p className="text-xs uppercase tracking-[0.4em] text-gray-500 mb-3">Welcome</p>
        <h1 className="text-5xl font-bold text-gray-900 mb-3">How would you like to work today?</h1>
        <p className="text-lg text-gray-600 mb-10">
          Pick one of the three main actions to get moving.
        </p>

        <div className="grid gap-6 md:grid-cols-3">
          <ActionCard
            title="Create library"
            description="Start a fresh session, stage seeds, and build a new library."
            cta="Start"
            onClick={handleCreateLibrary}
          />
          <ActionCard
            title="Edit library"
            description="Open an existing library and modify its contents."
            cta="Open editor"
            onClick={() => navigate('/libraries/edit')}
          />
          <ActionCard
            title="Load library"
            description="Load a saved library to use further in several use cases."
            cta="Browse libraries"
            onClick={() => navigate('/libraries')}
          />
        </div>

        <div className="mt-6">
          <button
            type="button"
            onClick={() => navigate('/workflow/other')}
            className="text-sm text-gray-500 hover:text-gray-800 underline underline-offset-4"
          >
            Other workflows…
          </button>
        </div>

        {error && <div className="mt-6 text-red-600 text-sm">Error: {error}</div>}
      </div>
    </div>
  )
}

function ActionCard({ title, description, cta, onClick }) {
  return (
    <div
      className="
        rounded-3xl border border-gray-200 p-6 
        bg-gradient-to-b from-white to-gray-50 
        shadow-md 
        hover:shadow-lg 
        hover:-translate-y-[2px] 
        active:translate-y-[1px]
        transition-all
      "
    >
      <h3 className="text-xl font-semibold text-gray-900 mb-2">{title}</h3>
      <p className="text-sm text-gray-500 mb-6">{description}</p>

      <Button
        className="
          rounded-full bg-gray-900 text-white 
          hover:bg-gray-800 
          transition-colors
        "
        onClick={onClick}
      >
        {cta}
      </Button>
    </div>
  )
}
