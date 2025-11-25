import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import Stepper from '@/components/Stepper'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { getSessionId, hydrateSessionFromQuery } from '@/shared/lib/session'

export default function LibraryCreationStartPage() {
  const navigate = useNavigate()
  const [sessionId, setSessionId] = useState(null)
  const [authorName, setAuthorName] = useState('')
  const workflowSteps = ['Add', 'Stage', 'Match', 'Library']

  useEffect(() => {
    const sid = getSessionId() || hydrateSessionFromQuery()
    if (!sid) {
      navigate('/')
      return
    }
    setSessionId(sid)
  }, [navigate])

  const startSeedsFlow = () => {
    if (!sessionId) return
    navigate('/create/staging')
  }

  const goToAuthorTopic = () => {
    if (!authorName.trim()) return
    navigate(`/author-topic-evolution?author=${encodeURIComponent(authorName.trim())}`)
  }

  return (
    <div className="min-h-[calc(100vh-160px)] bg-white">
      <div className="max-w-6xl mx-auto px-6 py-10">
        <div className="max-w-3xl mb-10">
          <p className="text-sm uppercase tracking-[0.3em] text-gray-500 mb-3">Library creation</p>
          <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">Choose how you want to build your library</h1>
          <p className="text-lg text-gray-600">
            Either start collecting seed papers for a library or explore how an individual author’s topics evolved.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

          <div
            className="
              rounded-3xl border border-gray-200 
              shadow-md hover:shadow-lg 
              hover:-translate-y-[2px] active:translate-y-[1px]
              transition-all 
              bg-gradient-to-b from-white to-slate-50 
              p-8 flex flex-col
            "
          >
            <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="text-2xl font-semibold text-gray-900">Seed staging</h2>
                <p className="text-sm text-gray-500">Collect and prepare papers before creating your library.</p>
              </div>
            </div>

            <div className="mt-4 space-y-3 text-sm">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-purple-500" />
                <span>Sources: Zotero collections, uploaded files, manual OpenAlex IDs</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-purple-500" />
                <span>Clean up metadata, filter, and check retraction flags in staging</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-purple-500" />
                <span>Run OpenAlex matching only when the seed list looks right</span>
              </div>
            </div>
            <div className="mb-5 mt-5 text-sm text-gray-600 leading-relaxed">
              Upload document files, connect to Zotero, or paste OpenAlex IDs, then review, filter, spot retracted papers,
              and decide which seeds move forward before running matching.
            </div>

            <Stepper currentStep={1} steps={workflowSteps} />

            <div className="mt-auto pt-6">
              <Button
                className="
                  w-full rounded-full bg-gray-900 text-white 
                  hover:bg-gray-800 hover:-translate-y-[1px] 
                  transition-all
                "
                onClick={startSeedsFlow}
                disabled={!sessionId}
              >
                Start staging seeds
              </Button>
            </div>
          </div>

          <div
            className="
              rounded-3xl border border-gray-200 
              p-8 bg-white 
              shadow-md hover:shadow-lg
              hover:-translate-y-[2px] active:translate-y-[1px]
              transition-all 
              flex flex-col
            "
          >
            <div className="mb-4">
              <h2 className="text-2xl font-semibold text-gray-900">Author evolution</h2>
              <p className="text-sm text-gray-500">See how a researcher’s focus changed over time.</p>
            </div>

            <label className="text-sm font-medium text-gray-700 mb-2" htmlFor="author-name">
              Author name
            </label>
            <Input
              id="author-name"
              placeholder="Ada Lovelace"
              value={authorName}
              onChange={(e) => setAuthorName(e.target.value)}
              className="mb-4"
            />

            <p className="text-sm text-gray-500 mb-6">
              Enter an author to open the topic evolution flow, configure the filters, and track how their work shifted across years.
            </p>

            <Button
              variant="outline"
              className="
                rounded-full border-gray-300 text-gray-800 
                hover:bg-gray-100 hover:-translate-y-[1px]
                transition-all
              "
              onClick={goToAuthorTopic}
              disabled={!authorName.trim()}
            >
              Explore author topics
            </Button>
          </div>

        </div>
      </div>
    </div>
  )
}
