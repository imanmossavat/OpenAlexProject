import { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { AlertCircle, Loader2, RefreshCcw } from 'lucide-react'

import apiClient from '@/shared/api/client'
import { endpoints } from '@/shared/api/endpoints'
import useCrawlerSession from '@/pages/crawler/hooks/useCrawlerSession'
import Stepper from '@/components/Stepper'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'

const steps = ['Keywords', 'Configuration', 'Run', 'Results']

const defaultAdvanced = {
  topic_model: 'NMF',
  num_topics: 20,
  save_figures: true,
  include_author_nodes: false,
  enable_retraction_watch: true,
  additional_ignored_venues: [],
  language: 'en',
}

export default function CrawlerConfigurationPage() {
  const navigate = useNavigate()
  const { sessionId, loading: loadingSession, error: sessionError } = useCrawlerSession()
  const [basicForm, setBasicForm] = useState({ max_iterations: 1, papers_per_iteration: 1 })
  const [advancedForm, setAdvancedForm] = useState(defaultAdvanced)
  const [loadingConfig, setLoadingConfig] = useState(true)
  const [error, setError] = useState(null)
  const [status, setStatus] = useState(null)
  const [saving, setSaving] = useState(false)
  const [showAdvanced, setShowAdvanced] = useState(false)
  const [newIgnoredVenue, setNewIgnoredVenue] = useState('')

  const mapResponseToForms = useCallback((config) => {
    const basic = {
      max_iterations: config?.max_iterations || 1,
      papers_per_iteration: config?.papers_per_iteration || 1,
    }
    setBasicForm(basic)

    const adv = {
      topic_model: config?.topic_model || defaultAdvanced.topic_model,
      num_topics: config?.num_topics || defaultAdvanced.num_topics,
      save_figures: typeof config?.save_figures === 'boolean' ? config.save_figures : defaultAdvanced.save_figures,
      include_author_nodes: typeof config?.include_author_nodes === 'boolean' ? config.include_author_nodes : defaultAdvanced.include_author_nodes,
      enable_retraction_watch: typeof config?.enable_retraction_watch === 'boolean' ? config.enable_retraction_watch : defaultAdvanced.enable_retraction_watch,
      additional_ignored_venues: config?.ignored_venues || [],
      language: config?.language || defaultAdvanced.language,
    }

    setAdvancedForm(adv)
  }, [])

  const loadConfiguration = useCallback(async () => {
    if (!sessionId) return
    setLoadingConfig(true)
    setError(null)
    const res = await apiClient('GET', `${endpoints.configuration}/${sessionId}/config`)
    if (res.error) {
      setError(res.error)
    } else {
      mapResponseToForms(res.data || {})
    }
    setLoadingConfig(false)
  }, [sessionId, mapResponseToForms])

  useEffect(() => {
    if (sessionId) loadConfiguration()
  }, [sessionId, loadConfiguration])

  const handleSaveBasic = async () => {
    setSaving(true)
    setError(null)
    const payload = {
      max_iterations: Number(basicForm.max_iterations) || 1,
      papers_per_iteration: Number(basicForm.papers_per_iteration) || 1,
    }
    const res = await apiClient('POST', `${endpoints.configuration}/${sessionId}/config/basic`, payload)
    if (res.error) {
      setError(res.error)
      setSaving(false)
      return false
    }
    setStatus('Basic configuration saved.')
    setSaving(false)
    return true
  }

  const handleSaveAdvanced = async () => {
    const payload = { ...advancedForm }
    const res = await apiClient('POST', `${endpoints.configuration}/${sessionId}/config/advanced`, payload)
    if (res.error) {
      setError(res.error)
      return false
    }
    setStatus('Configuration updated.')
    return true
  }

  const handleSaveAll = async () => {
    if (!sessionId) return
    setStatus(null)
    const okBasic = await handleSaveBasic()
    if (!okBasic) return
    if (showAdvanced) {
      setSaving(true)
      await handleSaveAdvanced()
      setSaving(false)
    }
  }

  const handleReset = async () => {
    if (!sessionId) return
    setSaving(true)
    const res = await apiClient('DELETE', `${endpoints.configuration}/${sessionId}/config`)
    if (res.error) {
      setError(res.error)
    } else {
      setStatus('Configuration reset.')
      mapResponseToForms({})
    }
    setSaving(false)
  }

  const handleNext = async () => {
    if (!sessionId) return
    if (!status) {
      await handleSaveAll()
    }
    navigate('/crawler/run')
  }

  const disabled = loadingSession || loadingConfig || saving

  const handleAddIgnoredVenue = () => {
    const value = newIgnoredVenue.trim()
    if (!value) return
    setAdvancedForm((prev) => {
      if (prev.additional_ignored_venues.includes(value)) return prev
      return {
        ...prev,
        additional_ignored_venues: [...prev.additional_ignored_venues, value],
      }
    })
    setNewIgnoredVenue('')
  }

  const handleRemoveIgnoredVenue = (value) => {
    setAdvancedForm((prev) => ({
      ...prev,
      additional_ignored_venues: prev.additional_ignored_venues.filter((item) => item !== value),
    }))
  }

  return (
    <div className="min-h-[calc(100vh-160px)] bg-white">
      <div className="max-w-5xl mx-auto px-6 py-12 space-y-8">
        <Stepper steps={steps} currentStep={2} />

        <div className="space-y-3">
          <p className="text-xs uppercase tracking-[0.4em] text-gray-500">Crawler workflow</p>
          <h1 className="text-4xl font-bold text-gray-900">Configure the crawler</h1>
          <p className="text-gray-600 text-lg">
            Set the core parameters for the crawl. Basic configuration is required; advanced settings are optional for fine-tuning topic modeling, graph output, and filtering.
          </p>
        </div>

        {sessionError ? (
          <div className="rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-red-700 flex gap-2 items-start">
            <AlertCircle className="w-4 h-4 mt-0.5" />
            <div>{sessionError}</div>
          </div>
        ) : null}

        {error ? (
          <div className="rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-red-700 flex gap-2 items-start">
            <AlertCircle className="w-4 h-4 mt-0.5" />
            <div>{error}</div>
          </div>
        ) : null}

        {status ? (
          <div className="rounded-2xl border border-green-200 bg-green-50 p-4 text-sm text-green-800">
            {status}
          </div>
        ) : null}

        <div className="rounded-3xl border border-gray-200 p-6 space-y-6">
          <h2 className="text-lg font-semibold text-gray-900">Basic Settings</h2>

          <div className="space-y-5">
            <div>
              <Label className="text-sm font-medium text-gray-800">Maximum iterations</Label>
              <Input
                type="number"
                min={1}
                value={basicForm.max_iterations}
                onChange={(e) =>
                  setBasicForm((prev) => ({ ...prev, max_iterations: Number(e.target.value) }))
                }
                disabled={disabled}
                className="mt-1 rounded-full shadow-md px-6 py-3 text-base border-gray-200 focus-visible:border-gray-400"
              />
              <p className="text-xs text-gray-500 mt-1">
                How many times the crawler will iterate through the paper network
              </p>
            </div>

            <div>
              <Label className="text-sm font-medium text-gray-800">Papers per iteration</Label>
              <Input
                type="number"
                min={1}
                value={basicForm.papers_per_iteration}
                onChange={(e) =>
                  setBasicForm((prev) => ({ ...prev, papers_per_iteration: Number(e.target.value) }))
                }
                disabled={disabled}
                className="mt-1 rounded-full shadow-md px-6 py-3 text-base border-gray-200 focus-visible:border-gray-400"
              />
              <p className="text-xs text-gray-500 mt-1">
                Number of papers to sample in each iteration
              </p>
            </div>
          </div>
        </div>

        <div className="rounded-3xl border border-gray-200 overflow-hidden">
          <button
            onClick={() => setShowAdvanced((prev) => !prev)}
            className="w-full flex items-center justify-between px-6 py-4 hover:bg-gray-50"
          >
            <div>
              <h2 className="text-lg font-semibold text-gray-900">Advanced Settings (Optional)</h2>
              <p className="text-sm text-gray-500">Customize advanced options</p>
            </div>

            <div className="flex items-center gap-3">
              <span className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded-full">Optional</span>

              <svg
                className={`w-5 h-5 text-gray-600 transition-transform ${
                  showAdvanced ? 'rotate-180' : ''
                }`}
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
              </svg>
            </div>
          </button>

          {showAdvanced && (
            <div className="px-6 pb-8 space-y-10">

              <div>
                <h3 className="text-xs font-semibold text-gray-500 tracking-wide mb-3">TOPIC MODELING</h3>

                <div className="space-y-4">
                  <div>
                    <Label className="text-sm font-medium text-gray-800">Algorithm</Label>
                    <Select
                      value={advancedForm.topic_model}
                      onValueChange={(value) =>
                        setAdvancedForm((prev) => ({ ...prev, topic_model: value }))
                      }
                      disabled={disabled}
                    >
                      <SelectTrigger className="mt-1 w-full rounded-full border border-gray-200 px-4 py-2 text-base">
                        <SelectValue placeholder="Select algorithm" />
                      </SelectTrigger>
                      <SelectContent className="rounded-2xl border border-gray-200 bg-white shadow-lg">
                        <SelectItem value="NMF">NMF (Non-negative Matrix Factorization)</SelectItem>
                        <SelectItem value="LDA">LDA (Latent Dirichlet Allocation)</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div>
                    <Label className="text-sm font-medium text-gray-800">Number of topics</Label>
                    <Input
                      type="number"
                      min={2}
                      max={100}
                      value={advancedForm.num_topics}
                      onChange={(e) =>
                        setAdvancedForm((prev) => ({ ...prev, num_topics: Number(e.target.value) }))
                      }
                      disabled={disabled}
                      className="mt-1 rounded-full shadow-md px-6 py-3 text-base border-gray-200 focus-visible:border-gray-400"
                    />
                  </div>
                </div>
              </div>

              <div>
                <h3 className="text-xs font-semibold text-gray-500 tracking-wide mb-3">GRAPH OPTIONS</h3>

                <div className="flex gap-3 items-start">
                  <input
                    type="checkbox"
                    checked={advancedForm.include_author_nodes}
                    onChange={(e) =>
                      setAdvancedForm((prev) => ({ ...prev, include_author_nodes: e.target.checked }))
                    }
                  />
                  <div>
                    <p className="text-sm text-gray-800">Include author nodes in graph</p>
                    <p className="text-xs text-gray-500">
                      Adds author relationships to the citation network
                    </p>
                  </div>
                </div>
              </div>

              <div>
                <h3 className="text-xs font-semibold text-gray-500 tracking-wide mb-3">ANALYSIS OPTIONS</h3>

                <div className="space-y-4">

                  <div className="flex gap-3 items-start">
                    <input
                      type="checkbox"
                      checked={advancedForm.enable_retraction_watch}
                      onChange={(e) =>
                        setAdvancedForm((prev) => ({ ...prev, enable_retraction_watch: e.target.checked }))
                      }
                    />
                    <div>
                      <p className="text-sm text-gray-800">Enable retraction watch</p>
                      <p className="text-xs text-gray-500">
                        Check for retracted papers in the network
                      </p>
                    </div>
                  </div>

                  <div className="flex gap-3 items-start">
                    <input
                      type="checkbox"
                      checked={advancedForm.save_figures}
                      onChange={(e) =>
                        setAdvancedForm((prev) => ({ ...prev, save_figures: e.target.checked }))
                      }
                    />
                    <div>
                      <p className="text-sm text-gray-800">Save topic modeling figures</p>
                      <p className="text-xs text-gray-500">
                        Generate PNG visualizations of topic models
                      </p>
                    </div>
                  </div>

                </div>
              </div>

              <div>
                <h3 className="text-xs font-semibold text-gray-500 tracking-wide mb-3">FILTERING OPTIONS</h3>

                <Label className="text-sm font-medium text-gray-800">Ignored venues</Label>
                <div className="mt-1 flex gap-2">
                  <Input
                    type="text"
                    placeholder="bioRxiv"
                    value={newIgnoredVenue}
                    onChange={(e) => setNewIgnoredVenue(e.target.value)}
                    disabled={disabled}
                    className="rounded-full shadow-md px-6 py-3 text-base border-gray-200 focus-visible:border-gray-400 placeholder:text-gray-400"
                  />
                  <Button
                    type="button"
                    className="rounded-full"
                    disabled={disabled || !newIgnoredVenue.trim()}
                    onClick={handleAddIgnoredVenue}
                  >
                    Add
                  </Button>
                </div>
                <p className="text-xs text-gray-500 mt-1">Papers from these venues will be excluded.</p>
                {advancedForm.additional_ignored_venues.length ? (
                  <div className="flex flex-wrap gap-2 mt-3">
                    {advancedForm.additional_ignored_venues.map((venue) => (
                      <span
                        key={venue}
                        onClick={() => handleRemoveIgnoredVenue(venue)}
                        className="px-3 py-1 rounded-full bg-gray-100 text-sm text-gray-800 cursor-pointer hover:bg-gray-200 transition"
                      >
                        {venue} ×
                      </span>
                    ))}
                  </div>
                ) : null}
              </div>

              <div>
                <Label className="text-sm font-medium text-gray-800">Language</Label>
                <Select
                  value={advancedForm.language}
                  onValueChange={(value) =>
                    setAdvancedForm((prev) => ({ ...prev, language: value }))
                  }
                  disabled={disabled}
                >
                  <SelectTrigger className="mt-1 w-full rounded-full border border-gray-200 px-4 py-2 text-base">
                    <SelectValue placeholder="Select language" />
                  </SelectTrigger>
                  <SelectContent className="rounded-2xl border border-gray-200 bg-white shadow-lg max-h-60">
                    {['en', 'es', 'fr', 'de', 'it', 'pt', 'nl', 'ru', 'zh', 'ja', 'ar'].map((lang) => (
                      <SelectItem key={lang} value={lang}>
                        {lang.toUpperCase()}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
          )}
        </div>

        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex gap-3">
            <Button variant="outline" className="rounded-full" onClick={handleReset} disabled={disabled}>
              <RefreshCcw className="w-4 h-4 mr-2" />
              Reset
            </Button>
            <Button className="rounded-full" onClick={handleSaveAll} disabled={disabled}>
              {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Save configuration'}
            </Button>
          </div>

          <Button
            className="rounded-full bg-gray-900 text-white disabled:opacity-40"
            onClick={handleNext}
            disabled={disabled || !!error}
          >
            Continue to run
          </Button>
        </div>
      </div>
    </div>
  )
}
