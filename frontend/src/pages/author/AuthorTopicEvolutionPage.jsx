import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { AlertCircle, ArrowLeft, Loader2, RefreshCcw } from 'lucide-react'

import apiClient from '@/shared/api/client'
import { endpoints } from '@/shared/api/endpoints'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import Stepper from '@/components/Stepper'
import useLibraryRootPreference from '@/pages/libraries/hooks/useLibraryRootPreference'
import { clearAuthorTopicResult, clearSelectedAuthor, loadSelectedAuthor, saveAuthorTopicResult } from './storage'

const defaultConfig = {
  modelType: 'NMF',
  numTopics: 6,
  timePeriodYears: 3,
  maxPapers: '',
  saveLibrary: false,
  libraryPath: '',
}

export default function AuthorTopicEvolutionPage() {
  const navigate = useNavigate()
  const [selectedAuthor, setSelectedAuthor] = useState(() => loadSelectedAuthor())
  const [config, setConfig] = useState(defaultConfig)
  const [runningAnalysis, setRunningAnalysis] = useState(false)
  const [analysisError, setAnalysisError] = useState(null)
  const { defaultRoot: defaultLibraryRoot } = useLibraryRootPreference()

  useEffect(() => {
    if (!selectedAuthor) {
      navigate('/author-topic-evolution/select')
    }
  }, [selectedAuthor, navigate])

  useEffect(() => {
    if (
      selectedAuthor &&
      config.saveLibrary &&
      !config.libraryPath &&
      defaultLibraryRoot
    ) {
      setConfig((prev) => ({
        ...prev,
        libraryPath: defaultLibraryRoot.trim(),
      }))
    }
  }, [config.saveLibrary, config.libraryPath, defaultLibraryRoot, selectedAuthor])

  if (!selectedAuthor) {
    return null
  }

  const handleConfigChange = (field, value) => {
    setConfig((prev) => ({
      ...prev,
      [field]: value,
    }))
  }

  const runAnalysis = async () => {
    if (!selectedAuthor) return
    setRunningAnalysis(true)
    setAnalysisError(null)

    const basePath = config.libraryPath.trim()
    const finalLibraryPath =
      config.saveLibrary && basePath
        ? buildFinalLibraryPath(basePath, selectedAuthor.name)
        : undefined

    const payload = {
      author_id: selectedAuthor.id,
      author_name: selectedAuthor.name,
      model_type: config.modelType,
      num_topics: Number(config.numTopics) || defaultConfig.numTopics,
      time_period_years: Number(config.timePeriodYears) || defaultConfig.timePeriodYears,
      api_provider: 'openalex',
      max_papers: config.maxPapers ? Number(config.maxPapers) : undefined,
      save_library: Boolean(config.saveLibrary && finalLibraryPath),
      library_path: finalLibraryPath,
    }

    const { data, error } = await apiClient('POST', `${endpoints.authorTopicEvolution}/start`, payload)
    if (error) {
      setAnalysisError(error)
    } else {
      saveAuthorTopicResult({
        ...data,
        timestamp: Date.now(),
      })
      navigate('/author-topic-evolution/results')
    }
    setRunningAnalysis(false)
  }

  const changeAuthor = () => {
    const query = selectedAuthor?.name ? `?author=${encodeURIComponent(selectedAuthor.name)}` : ''
    clearSelectedAuthor()
    clearAuthorTopicResult()
    navigate(`/author-topic-evolution/select${query}`)
  }

  return (
    <div className="min-h-[calc(100vh-160px)] bg-white">
      <div className="max-w-6xl mx-auto px-6 py-10">
        <div className="max-w-5xl mx-auto space-y-8">
          <Stepper
            steps={['Select author', 'Configure', 'Analyze', 'Results']}
            currentStep={2}
          />

          <div className="flex flex-col gap-4 border-b border-gray-100 pb-6">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div className="space-y-2">
                <p className="text-xs uppercase tracking-[0.4em] text-gray-500">Author topic evolution</p>
                <h1 className="text-4xl font-bold text-gray-900">Configure the analysis</h1>
                <p className="text-lg text-gray-600">
                  Adjust the modeling inputs, choose how periods are grouped, and run the evolution job.
                </p>
              </div>
              <Button
                variant="ghost"
                className="text-gray-600 hover:text-gray-900"
                onClick={changeAuthor}
              >
                <ArrowLeft className="mr-2 h-4 w-4" />
                Pick a different author
              </Button>
            </div>

            <div className="rounded-2xl border border-gray-200 bg-gray-50 px-4 py-3 text-sm text-gray-700 flex flex-wrap gap-3 items-center">
              <span className="font-semibold text-gray-900">{selectedAuthor.name}</span>
              <span className="text-xs font-semibold uppercase tracking-[0.25em] text-gray-500">{selectedAuthor.id}</span>
              <span className="text-gray-500">
                {selectedAuthor.works_count?.toLocaleString()} works · {selectedAuthor.cited_by_count?.toLocaleString()} citations
              </span>
              {selectedAuthor.orcid && <span className="text-gray-500">ORCID {selectedAuthor.orcid}</span>}
            </div>
          </div>

        </div>

        <div className="max-w-5xl mx-auto space-y-6 mt-6">
          {analysisError && (
            <div className="flex items-start gap-2 rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
              <AlertCircle className="h-4 w-4 mt-0.5" />
              <span>{analysisError}</span>
            </div>
          )}

          <AnalysisConfigurationCard
            disabled={runningAnalysis}
            config={config}
            onChange={handleConfigChange}
            onRun={runAnalysis}
            running={runningAnalysis}
          />

        </div>
      </div>
    </div>
  )
}

function AnalysisConfigurationCard({ disabled, config, onChange, onRun, running }) {
  return (
    <div className="rounded-3xl border border-gray-200 p-6 space-y-6 bg-white">
      <div className="space-y-2">
        <h2 className="text-xl font-semibold text-gray-900">Model configuration</h2>
        <p className="text-sm text-gray-500">
          Choose the modeling strategy, topic count, and period size. Saving as a library keeps the files permanently.
        </p>
      </div>

      <div className="grid gap-5 md:grid-cols-2">
        <ConfigField label="Topic model">
          <Select
            value={config.modelType}
            onValueChange={(value) => onChange('modelType', value)}
          >
            <SelectTrigger className="rounded-2xl border-gray-200 px-4 py-3 text-sm">
              <SelectValue />
            </SelectTrigger>
            <SelectContent className="rounded-2xl border border-gray-200 bg-white shadow-lg">
              <SelectItem value="NMF">NMF (Non-negative Matrix Factorization)</SelectItem>
              <SelectItem value="LDA">LDA (Latent Dirichlet Allocation)</SelectItem>
            </SelectContent>
          </Select>
        </ConfigField>
        <ConfigField label="Number of topics">
          <Input
            type="number"
            min={3}
            max={30}
            value={config.numTopics}
            onChange={(e) => onChange('numTopics', e.target.value)}
            className="rounded-2xl border-gray-200 px-4 py-3 text-sm"
          />
        </ConfigField>

      </div>

      <div className="grid gap-5 md:grid-cols-2">
        <ConfigField label="Years per period">
          <Input
            type="number"
            min={1}
            max={10}
            value={config.timePeriodYears}
            onChange={(e) => onChange('timePeriodYears', e.target.value)}
            className="rounded-2xl border-gray-200 px-4 py-3 text-sm"
          />
        </ConfigField>

        <ConfigField label="Cap papers (optional)">
          <Input
            type="number"
            min={10}
            placeholder="Analyze all papers"
            value={config.maxPapers}
            onChange={(e) => onChange('maxPapers', e.target.value)}
            className="rounded-2xl border-gray-200 px-4 py-3 text-sm"
          />
        </ConfigField>

      </div>

      <div className="rounded-2xl border border-gray-200 p-4">
          <label className="flex cursor-pointer items-center gap-3 text-sm text-gray-700">
            <input
              type="checkbox"
              checked={config.saveLibrary}
              onChange={(e) => onChange('saveLibrary', e.target.checked)}
              className="h-4 w-4 rounded border-gray-300 text-gray-900 focus:ring-gray-900"
            />
            Save as a permanent library
          </label>
          {config.saveLibrary && (
            <Input
              placeholder="Absolute path for the new library"
              value={config.libraryPath}
              onChange={(e) => onChange('libraryPath', e.target.value)}
              className="mt-3 rounded-2xl border-gray-200 px-4 py-3 text-sm"
            />
          )}
        </div>

      <div className="flex justify-end">
        <Button
          disabled={disabled}
          className="rounded-full bg-gray-900 px-8 text-white hover:bg-gray-800 disabled:opacity-60"
          onClick={onRun}
        >
          {running ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Analyzing
            </>
          ) : (
            <>
              <RefreshCcw className="mr-2 h-4 w-4" />
              Run analysis
            </>
          )}
        </Button>
      </div>
    </div>
  )
}

function ConfigField({ label, children }) {
  return (
    <div>
      <label className="text-xs font-semibold uppercase tracking-wide text-gray-500">{label}</label>
      <div className="mt-1">{children}</div>
    </div>
  )
}

function buildFinalLibraryPath(rootPath, authorName) {
  if (!rootPath) return undefined
  const trimmedRoot = rootPath.replace(/[\\/]+$/, '')
  const folderName = buildAuthorFolderName(authorName)
  const separator =
    trimmedRoot.includes('\\') && !trimmedRoot.includes('/')
      ? '\\'
      : '/'
  return `${trimmedRoot}${separator}${folderName}`
}

function buildAuthorFolderName(authorName) {
  const sanitizedName = (authorName || 'author')
    .toLowerCase()
    .replace(/[^a-z0-9]+/gi, '-')
    .replace(/^-+|-+$/g, '')
  const timestamp = new Date().toISOString().replace(/[^0-9]/g, '')
  return `${sanitizedName || 'author'}-topic-evolution-${timestamp}`
}
