import { useMemo, useState } from 'react'
import { Loader2, RefreshCcw } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

import { Button } from '@/components/ui/button'
import apiClient from '@/shared/api/client'
import { endpoints } from '@/shared/api/endpoints'
import { setSessionId } from '@/shared/lib/session'
import { deriveNameFromPath, isAbsolutePath } from '@/pages/libraries/utils'

import useExperimentDiscovery from './hooks/useExperimentDiscovery'
import useExperimentRootPreference from './hooks/useExperimentRootPreference'
import ExperimentSearchBar from './components/ExperimentSearchBar'
import ExperimentGridSection from './components/ExperimentGridSection'
import ExperimentRootPanel from './components/ExperimentRootPanel'
import CustomExperimentPathPanel from './components/CustomExperimentPathPanel'
import ExperimentActionDialog from './components/ExperimentActionDialog'

export default function CrawlerRerunPage() {
  const navigate = useNavigate()
  const {
    experiments,
    loading,
    error,
    page,
    pageSize,
    total,
    hasNextPage,
    rootPath: discoveryRoot,
    searchInput,
    setSearchInput,
    clearSearch,
    goToNextPage,
    reload,
  } = useExperimentDiscovery({ pageSize: 9 })
  const {
    defaultRoot,
    rootInput,
    setRootInput,
    rootError,
    rootLoading,
    rootSaving,
    rootPathHasValue,
    rootPathValid,
    saveRoot,
    resetRoot,
    clearRootError,
  } = useExperimentRootPreference()

  const [selectedExperiment, setSelectedExperiment] = useState(null)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [loadingAction, setLoadingAction] = useState(null)
  const [actionError, setActionError] = useState(null)
  const [manualPath, setManualPath] = useState('')
  const [manualError, setManualError] = useState(null)

  const manualPathValid = useMemo(() => isAbsolutePath(manualPath), [manualPath])

  const displayedRoot = useMemo(() => discoveryRoot || defaultRoot, [discoveryRoot, defaultRoot])

  const handleSaveRoot = async () => {
    const ok = await saveRoot()
    if (ok) reload()
  }

  const handleResetRoot = async () => {
    await resetRoot()
    reload()
  }

  const handleSelectExperiment = (experiment) => {
    setSelectedExperiment(experiment)
    setDialogOpen(true)
    setActionError(null)
  }

  const handleManualSubmit = () => {
    if (!manualPathValid) {
      setManualError('Please enter an absolute path.')
      return
    }
    setManualError(null)
    setSelectedExperiment({
      job_id: manualPath,
      name: deriveNameFromPath(manualPath),
      display_name: deriveNameFromPath(manualPath),
      manualPath,
      library_path: manualPath,
    })
    setDialogOpen(true)
    setActionError(null)
  }

  const startRerunSession = async () => {
    const res = await apiClient('POST', `${endpoints.seedsSession}/start`, { use_case: 'crawler_rerun' })
    if (res.error || !res.data?.session_id) throw new Error(res.error || 'Unable to start rerun session')
    return res.data.session_id
  }

  const loadExperimentConfig = async (sessionId, jobId) => {
    const res = await apiClient('POST', `${endpoints.crawlerReruns}/experiments/${jobId}/load`, {
      session_id: sessionId,
    })
    if (res.error) throw new Error(res.error)
    return res.data?.experiment
  }

  const loadExperimentByPath = async (sessionId, experimentPath) => {
    const res = await apiClient('POST', `${endpoints.crawlerReruns}/experiments/load-by-path`, {
      session_id: sessionId,
      experiment_path: experimentPath,
    })
    if (res.error) throw new Error(res.error)
    return res.data?.experiment
  }

  const runCrawlerJob = async (sessionId, experimentSummary) => {
    const payload = {
      use_case: 'crawler_rerun',
      library_path: experimentSummary?.library_path || null,
      library_name: experimentSummary?.library_name || null,
    }
    const res = await apiClient('POST', `${endpoints.crawler}/${sessionId}/start`, payload)
    if (res.error || !res.data?.job_id) throw new Error(res.error || 'Unable to start crawler job')
    return res.data.job_id
  }

  const handleRerunWithEdits = async () => {
    if (!selectedExperiment) return
    setLoadingAction('edit')
    setActionError(null)
    try {
      const sessionId = await startRerunSession()
      if (selectedExperiment.manualPath) {
        await loadExperimentByPath(sessionId, selectedExperiment.manualPath)
      } else {
        await loadExperimentConfig(sessionId, selectedExperiment.job_id)
      }
      setSessionId(sessionId, { useCase: 'crawler_rerun' })
      setDialogOpen(false)
      navigate('/crawler/keywords')
    } catch (err) {
      setActionError(err.message || 'Unable to load experiment.')
    } finally {
      setLoadingAction(null)
    }
  }

  const handleRerunNow = async () => {
    if (!selectedExperiment) return
    setLoadingAction('now')
    setActionError(null)
    try {
      const sessionId = await startRerunSession()
      const summary = selectedExperiment.manualPath
        ? await loadExperimentByPath(sessionId, selectedExperiment.manualPath)
        : await loadExperimentConfig(sessionId, selectedExperiment.job_id)
      const jobId = await runCrawlerJob(sessionId, summary)
      setDialogOpen(false)
      setSelectedExperiment(null)
      navigate(`/crawler/results?job=${encodeURIComponent(jobId)}`)
    } catch (err) {
      setActionError(err.message || 'Unable to start crawler job.')
    } finally {
      setLoadingAction(null)
    }
  }

  return (
    <div className="min-h-[calc(100vh-160px)] bg-white">
      <div className="max-w-6xl mx-auto px-6 py-12 space-y-10">
        <header className="space-y-4">
          <p className="text-xs uppercase tracking-[0.4em] text-gray-500">Crawler reruns</p>
          <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
            <div>
              <h1 className="text-4xl font-bold text-gray-900 mb-2">Reuse a saved crawler configuration</h1>
              <p className="text-gray-600 text-lg max-w-3xl">
                Pick an experiment to re-run immediately or load it into the crawler wizard to make changes.
              </p>
              {displayedRoot ? (
                <p className="text-sm text-gray-500 mt-2">Scanning: {displayedRoot}</p>
              ) : (
                <p className="text-sm text-gray-500 mt-2">Scanning default ArticleCrawler experiments folder.</p>
              )}
            </div>
            <Button variant="outline" className="rounded-full" onClick={reload} disabled={loading}>
              {loading ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <RefreshCcw className="w-4 h-4 mr-2" />}
              Refresh list
            </Button>
          </div>
        </header>

        <section className="grid gap-8 lg:grid-cols-3">
          <div className="lg:col-span-2 space-y-4">
            <ExperimentSearchBar value={searchInput} onChange={setSearchInput} onClear={clearSearch} />
            <ExperimentGridSection
              experiments={experiments}
              loading={loading}
              error={error}
              page={page}
              pageSize={pageSize}
              total={total}
              hasNextPage={hasNextPage}
              onPageChange={goToNextPage}
              onRetry={reload}
              onSelectExperiment={handleSelectExperiment}
            />
          </div>
          <div className="space-y-6">
            <ExperimentRootPanel
              defaultRoot={defaultRoot}
              rootInput={rootInput}
              onChange={(value) => {
                setRootInput(value)
                clearRootError()
              }}
              rootError={rootError}
              rootLoading={rootLoading}
              rootSaving={rootSaving}
              onSave={handleSaveRoot}
              onReset={handleResetRoot}
              canSave={rootPathHasValue && rootPathValid}
            />
            <CustomExperimentPathPanel
              manualPath={manualPath}
              onChange={setManualPath}
              manualError={manualError}
              onSubmit={handleManualSubmit}
              isValidPath={manualPathValid}
            />
          </div>
        </section>
      </div>

      <ExperimentActionDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        experiment={selectedExperiment}
        onRerunNow={handleRerunNow}
        onRerunWithEdits={handleRerunWithEdits}
        loadingAction={loadingAction}
        error={actionError}
      />
    </div>
  )
}
