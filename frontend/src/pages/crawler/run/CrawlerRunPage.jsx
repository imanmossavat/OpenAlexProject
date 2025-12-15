import { useCallback, useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { AlertCircle, BookOpenCheck, Loader2, Play } from 'lucide-react'

import apiClient from '@/shared/api/client'
import { endpoints } from '@/shared/api/endpoints'
import useCrawlerSession from '@/pages/crawler/hooks/useCrawlerSession'
import Stepper from '@/components/Stepper'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'

const steps = ['Keywords', 'Configuration', 'Run', 'Results']
const JOB_STORAGE_KEY = 'crawler_last_job_id'

export default function CrawlerRunPage() {
  const navigate = useNavigate()
  const { sessionId, loading: loadingSession, error: sessionError } = useCrawlerSession()
  const [keywords, setKeywords] = useState([])
  const [config, setConfig] = useState(null)
  const [libraryDetails, setLibraryDetails] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [experimentName, setExperimentName] = useState('crawler-experiment')
  const [finalizeMessage, setFinalizeMessage] = useState(null)
  const [finalizeSummary, setFinalizeSummary] = useState(null)
  const [starting, setStarting] = useState(false)
  const [finalizing, setFinalizing] = useState(false)

  const hasSummary = Boolean(finalizeSummary)

  const loadData = useCallback(async () => {
    if (!sessionId) return
    setLoading(true)
    setError(null)
    const [kw, cfg, lib] = await Promise.all([
      apiClient('GET', `${endpoints.keywords}/${sessionId}/keywords`),
      apiClient('GET', `${endpoints.configuration}/${sessionId}/config`),
      apiClient('GET', `${endpoints.library}/${sessionId}/contents`),
    ])
    if (kw.error) setError(kw.error)
    else setKeywords(Array.isArray(kw.data?.keywords) ? kw.data.keywords : [])

    if (cfg.error) setError((prev) => prev || cfg.error)
    else setConfig(cfg.data)

    if (lib.error) {
      if (typeof lib.error === 'string' && lib.error.toLowerCase().includes('no library selected')) {
        setLibraryDetails(null)
      } else {
        setError((prev) => prev || lib.error)
      }
    } else {
      setLibraryDetails({
        name: lib.data?.name,
        path: lib.data?.path,
        total_papers: lib.data?.total_papers,
      })
    }

    setLoading(false)
  }, [sessionId])

  useEffect(() => {
    if (sessionId) loadData()
  }, [sessionId, loadData])

  const handleFinalize = async () => {
    if (!sessionId) return null
    setFinalizing(true)
    setError(null)
    const payload = {
      experiment_name: experimentName.trim() || 'crawler-experiment',
      library_path: libraryDetails?.path,
      library_name: libraryDetails?.name,
    }
    const res = await apiClient('POST', `${endpoints.configuration}/${sessionId}/config/finalize`, payload)
    if (res.error) {
      setError(res.error)
      setFinalizing(false)
      return null
    }
    setFinalizeMessage(res.data?.message || 'Configuration finalized.')
    setFinalizeSummary(res.data)
    setFinalizing(false)
    return res.data
  }

  const handleStartCrawler = async () => {
    if (!sessionId) return
    setStarting(true)
    setError(null)
    if (!hasSummary) {
      const summary = await handleFinalize()
      if (!summary) {
        setStarting(false)
        return
      }
    }
    const payload = {
      use_case: 'crawler_wizard',
      library_path: libraryDetails?.path,
      library_name: libraryDetails?.name,
    }
    const res = await apiClient('POST', `${endpoints.crawler}/${sessionId}/start`, payload)
    if (res.error || !res.data?.job_id) {
      setError(res.error || 'Unable to start crawler job')
      setStarting(false)
      return
    }
    try {
      localStorage.setItem(JOB_STORAGE_KEY, res.data.job_id)
    } catch (e) {
      // ignore storage errors
    }
    navigate(`/crawler/results?job=${encodeURIComponent(res.data.job_id)}`)
  }

  const summaryItems = useMemo(() => {
    if (!finalizeSummary) return []
    return [
      { label: 'Experiment', value: finalizeSummary.experiment_name },
      { label: 'Seeds', value: finalizeSummary.total_seeds },
      { label: 'Keywords', value: finalizeSummary.total_keywords },
      { label: 'Iterations', value: finalizeSummary.max_iterations },
      { label: 'Papers/iteration', value: finalizeSummary.papers_per_iteration },
    ]
  }, [finalizeSummary])

  return (
    <div className="min-h-[calc(100vh-160px)] bg-white">
      <div className="max-w-5xl mx-auto px-6 py-12 space-y-8">
        <Stepper currentStep={3} steps={steps} />

        <div className="space-y-3">
          <p className="text-xs uppercase tracking-[0.4em] text-gray-500">Crawler workflow</p>
          <h1 className="text-4xl font-bold text-gray-900">Finalize and run the crawler</h1>
          <p className="text-gray-600 text-lg">
            Review your configuration, choose an experiment name, and start the crawler. We&apos;ll keep you updated on
            progress and deliver the results once the crawl completes.
          </p>
        </div>

        {sessionError ? <Message type="error" text={sessionError} /> : null}
        {error ? <Message type="error" text={error} /> : null}
        {finalizeMessage ? <Message type="success" text={finalizeMessage} /> : null}

        <div className="bg-white rounded-3xl border border-gray-200 shadow-sm p-6 space-y-4">
          <h2 className="text-2xl font-semibold text-gray-900">Finalize experiment</h2>
          <p className="text-sm text-gray-600">
            Give this run a descriptive name, then finalize to capture a summary before launching the crawler.
          </p>
          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <label className="text-sm font-semibold text-gray-700">Experiment name</label>
              <Input
                type="text"
                value={experimentName}
                onChange={(e) => setExperimentName(e.target.value)}
                disabled={finalizing}
                className="mt-1 rounded-full shadow-md px-6 py-3 text-base border-gray-200 focus-visible:border-gray-400 placeholder:text-gray-400"
              />
            </div>
            <div className="text-sm text-gray-600">
              <p className="font-semibold mb-1">Finalization summary</p>
              {summaryItems.length ? (
                <ul className="space-y-1">
                  {summaryItems.map((item) => (
                    <li key={item.label} className="flex justify-between">
                      <span className="text-gray-500">{item.label}</span>
                      <span className="font-semibold">{item.value}</span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-gray-500">Finalize to generate a summary.</p>
              )}
            </div>
          </div>
          <div className="flex flex-wrap gap-3">
            <Button
              variant="outline"
              className="rounded-full"
              onClick={handleFinalize}
              disabled={finalizing || loading || loadingSession}
            >
              {finalizing ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <BookOpenCheck className="w-4 h-4 mr-2" />}
              Update summary
            </Button>
            <Button
              className="rounded-full bg-gray-900 text-white"
              onClick={handleStartCrawler}
              disabled={starting || loading || loadingSession}
            >
              {starting ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Play className="w-4 h-4 mr-2" />}
              Start crawler
            </Button>
          </div>
        </div>

        <div className="grid gap-6 md:grid-cols-2">
          <SummaryCard title="Keywords" loading={loading || loadingSession}>
            {keywords.length ? (
              <ul className="list-disc ml-4 text-sm text-gray-700 space-y-1">
                {keywords.map((kw) => (
                  <li key={kw}>{kw}</li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-gray-500">All papers (no keyword filters).</p>
            )}
          </SummaryCard>

          <SummaryCard title="Configuration" loading={loading || loadingSession}>
            {config ? (
              <div className="text-sm text-gray-700 space-y-1">
                <p>
                  Iterations:{' '}
                  <span className="font-semibold">
                    {config.max_iterations} × {config.papers_per_iteration} papers
                  </span>
                </p>
                <p>
                  Topic model:{' '}
                  <span className="font-semibold">
                    {config.topic_model} ({config.num_topics} topics)
                  </span>
                </p>
                <p>
                  Retraction watch:{' '}
                  <span className="font-semibold">
                    {config.enable_retraction_watch ? 'Enabled' : 'Disabled'}
                  </span>
                </p>
              </div>
            ) : (
              <p className="text-sm text-gray-500">No configuration found.</p>
            )}
          </SummaryCard>
        </div>

        <SummaryCard title="Library" loading={loading || loadingSession}>
          {libraryDetails ? (
            <div className="text-sm text-gray-700 space-y-1">
              <p className="font-semibold">{libraryDetails.name || 'Library'}</p>
              <p className="font-mono break-all">{libraryDetails.path}</p>
              <p className="text-gray-500">{libraryDetails.total_papers} papers</p>
            </div>
          ) : (
            <p className="text-sm text-gray-500">No library attached.</p>
          )}
        </SummaryCard>

        {/* rest of page unchanged */}
      </div>
    </div>
  )
}

function SummaryCard({ title, loading, children }) {
  return (
    <div className="bg-white rounded-3xl border border-gray-200 shadow-sm p-6">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
        {loading ? <Loader2 className="w-4 h-4 animate-spin text-gray-500" /> : null}
      </div>
      {children}
    </div>
  )
}

function Message({ type, text }) {
  const styles =
    type === 'error'
      ? 'border-red-200 bg-red-50 text-red-800'
      : 'border-green-200 bg-green-50 text-green-800'
  return (
    <div className={`rounded-2xl border p-4 text-sm ${styles} flex gap-2 items-start`}>
      {type === 'error' ? <AlertCircle className="w-4 h-4 mt-0.5" /> : null}
      <div>{text}</div>
    </div>
  )
}
