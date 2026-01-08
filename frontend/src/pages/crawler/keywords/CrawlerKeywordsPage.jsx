import { useCallback, useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { AlertCircle, CheckCircle2, Info, Loader2, Plus, Trash2, X } from 'lucide-react'

import apiClient from '@/shared/api/client'
import { endpoints } from '@/shared/api/endpoints'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import useCrawlerSession from '@/pages/crawler/hooks/useCrawlerSession'
import Stepper from '@/components/Stepper'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'

const steps = ['Keywords', 'Configuration', 'Run', 'Results']

export default function CrawlerKeywordsPage() {
  const navigate = useNavigate()
  const { sessionId, loading: loadingSession, error: sessionError, ensureSession } = useCrawlerSession()
  const [keywords, setKeywords] = useState([])
  const [expression, setExpression] = useState('')
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [feedback, setFeedback] = useState(null)
  const [error, setError] = useState(null)
  const [syntaxOpen, setSyntaxOpen] = useState(false)

  const hasKeywords = keywords.length > 0

  const fetchKeywords = useCallback(async () => {
    if (!sessionId) return
    setLoading(true)
    setError(null)
    const res = await apiClient('GET', `${endpoints.keywords}/${sessionId}/keywords`)
    if (res.error) {
      setError(res.error)
      setKeywords([])
    } else {
      setKeywords(Array.isArray(res.data?.keywords) ? res.data.keywords : [])
    }
    setLoading(false)
  }, [sessionId])

  useEffect(() => {
    if (sessionId) fetchKeywords()
  }, [sessionId, fetchKeywords])

  const handleAddKeyword = async () => {
    if (!sessionId || !expression.trim()) return
    setSaving(true)
    setError(null)
    setFeedback(null)
    const res = await apiClient('POST', `${endpoints.keywords}/${sessionId}/keywords`, {
      expression: expression.trim(),
    })
    if (res.error) {
      setError(res.error)
    } else {
      setKeywords((prev) => [...prev, expression.trim()])
      setExpression('')
    }
    setSaving(false)
  }

  const handleRemoveKeyword = async (value) => {
    if (!sessionId) return
    setSaving(true)
    setError(null)
    const res = await apiClient('DELETE', `${endpoints.keywords}/${sessionId}/keywords/item`, {
      expression: value,
    })
    if (res.error) {
      setError(res.error)
    } else {
      setKeywords(Array.isArray(res.data?.keywords) ? res.data.keywords : [])
    }
    setSaving(false)
  }

  const handleClearAll = async () => {
    if (!sessionId) return
    setSaving(true)
    setError(null)
    const res = await apiClient('DELETE', `${endpoints.keywords}/${sessionId}/keywords/all`)
    if (res.error) {
      setError(res.error)
    } else {
      setKeywords([])
    }
    setSaving(false)
  }

  const handleFinalize = async () => {
    if (!sessionId) {
      await ensureSession()
      return
    }
    setSaving(true)
    setError(null)
    const res = await apiClient('POST', `${endpoints.keywords}/${sessionId}/keywords/finalize`)
    if (res.error) {
      setError(res.error)
    } else {
      setFeedback(res.data?.message || 'Keywords finalized')
      navigate('/crawler/configuration')
    }
    setSaving(false)
  }

  const disabledAdd = saving || !expression.trim()

  return (
    <div className="min-h-[calc(100vh-160px)] bg-white">
      <div className="max-w-5xl mx-auto px-6 py-12 space-y-8">
        <Stepper steps={steps} currentStep={1} />

        <div className="space-y-3">
          <p className="text-xs uppercase tracking-[0.4em] text-gray-500">Crawler workflow</p>
          <h1 className="text-4xl font-bold text-gray-900">Define your keyword filters</h1>
          <p className="text-gray-600 text-lg">
            Add keywords or boolean expressions (AND, OR, NOT, parentheses) to guide the crawler.
          </p>
        </div>

        {sessionError ? (
          <div className="rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-red-700 flex gap-3 items-start">
            <AlertCircle className="w-4 h-4 mt-0.5" />
            <div>
              <p className="font-semibold mb-1">Unable to start crawler session</p>
              <p>{sessionError}</p>
            </div>
          </div>
        ) : null}

        {feedback ? (
          <div className="rounded-2xl border border-green-200 bg-green-50 p-4 text-sm text-green-800 flex gap-2 items-center">
            <CheckCircle2 className="w-4 h-4" />
            <span>{feedback}</span>
          </div>
        ) : null}

        <div className="space-y-2">
          <div className="flex flex-col gap-3 md:flex-row md:items-end">
            <div className="flex-1">
              <Label htmlFor="expression" className="text-sm font-semibold text-gray-700">
                Keyword or boolean expression
              </Label>
              <Input
                id="expression"
                type="text"
                placeholder="(fake news OR misinformation) AND NOT satire"
                value={expression}
                onChange={(e) => setExpression(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !disabledAdd) {
                    e.preventDefault()
                    handleAddKeyword()
                  }
                }}
                className="mt-1 rounded-full shadow-md px-6 py-3 text-base border-gray-200 focus-visible:border-gray-400 placeholder:text-gray-400"
                disabled={saving || loadingSession}
              />
            </div>
            <div className="flex flex-col md:w-48 gap-2 md:justify-end">
              <Button
                type="button"
                variant="ghost"
                className="text-xs text-purple-600 hover:text-purple-700 justify-start"
                onClick={() => setSyntaxOpen(true)}
              >
                <Info className="w-4 h-4 mr-1" /> Syntax help
              </Button>
              <Button
                className="rounded-full px-4 py-2 text-sm"
                onClick={handleAddKeyword}
                disabled={disabledAdd}
              >
                {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4 mr-2" />}
                Add keyword
              </Button>
            </div>
          </div>
          <p className="text-xs text-gray-500">
            Tips: Use AND/OR/NOT for boolean logic. Parentheses help group expressions.
          </p>
        </div>

        {error ? (
          <div className="rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-red-700 flex gap-3 items-start">
            <AlertCircle className="w-4 h-4 mt-0.5" />
            <div>{error}</div>
          </div>
        ) : null}

        {hasKeywords ? (
          <div className="bg-white rounded-3xl border border-gray-200 shadow-sm p-6">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="text-xl font-semibold text-gray-900">Current keywords</h2>
                <p className="text-sm text-gray-500">
                  {loading ? 'Loading keywords…' : 'Click a keyword to remove it.'}
                </p>
              </div>
              <Button
                variant="outline"
                className="rounded-full"
                onClick={handleClearAll}
                disabled={!hasKeywords || saving}
              >
                <Trash2 className="w-4 h-4 mr-2" />
                Clear all
              </Button>
            </div>
            <div className="flex flex-wrap gap-2">
              {keywords.map((kw) => (
                <button
                  key={kw}
                  type="button"
                  onClick={() => handleRemoveKeyword(kw)}
                  className="px-3 py-1 rounded-full bg-gray-100 text-sm text-gray-800 flex items-center gap-1 hover:bg-gray-200 transition"
                  disabled={saving}
                >
                  <span>{kw}</span>
                  <X className="w-3 h-3" />
                </button>
              ))}
            </div>
          </div>
        ) : null}

        <div className="flex justify-end gap-3">
          <Button
            className="rounded-full bg-gray-900 text-white disabled:opacity-40"
            onClick={handleFinalize}
            disabled={saving || loadingSession}
          >
            Continue to configuration
          </Button>
        </div>
      </div>

      <Dialog open={syntaxOpen} onOpenChange={setSyntaxOpen}>
        <DialogContent className="bg-white max-w-xl">
          <DialogHeader>
            <DialogTitle className="text-xl font-semibold">Syntax help</DialogTitle>
          </DialogHeader>

          <div className="space-y-6 text-sm text-gray-700 max-h-[70vh] overflow-y-auto pr-2">
            <div className="space-y-3">
              <h3 className="font-semibold text-gray-800">Boolean Operators</h3>
              <div className="border border-gray-200 rounded-xl p-4 space-y-3">
                <p>
                  <span className="text-purple-600 font-medium">machine learning AND healthcare</span>
                  <br />
                  Papers containing both “machine learning” AND “Healthcare”
                </p>
                <p>
                  <span className="text-purple-600 font-medium">neural networks OR deep learning</span>
                  <br />
                  Papers containing either “neural networks” OR “deep learning”
                </p>
                <p>
                  <span className="text-purple-600 font-medium">AI NOT robotics</span>
                  <br />
                  Papers about “AI” but NOT “robotics”
                </p>
              </div>
            </div>

            <div className="space-y-3">
              <h3 className="font-semibold text-gray-800">Group with Parentheses</h3>
              <div className="border border-gray-200 rounded-xl p-4 space-y-3">
                <p>
                  <span className="text-purple-600 font-medium">(cancer OR tumor) AND detection</span>
                  <br />
                  Papers about “cancer” OR “tumor” that also mention “detection”
                </p>
                <p>
                  <span className="text-purple-600 font-medium">Covid-19 AND (vaccine OR treatment OR prevention)</span>
                  <br />
                  Papers about COVID-19 AND any of: vaccine, treatment, or prevention
                </p>
              </div>
            </div>

            <div className="space-y-3">
              <h3 className="font-semibold text-gray-800">Complex Examples</h3>
              <div className="border border-gray-200 rounded-xl p-4 space-y-4">
                <p>
                  <span className="text-purple-600 font-medium">
                    ("machine learning" OR "deep learning") AND (medical OR healthcare OR clinical)
                  </span>
                  <br />
                  Papers about ML/DL in medical contexts
                </p>
                <p>
                  <span className="text-purple-600 font-medium">quantum AND (computing OR algorithm) NOT cryptography</span>
                  <br />
                  Quantum computing or algorithms, excluding cryptography papers
                </p>
                <p>
                  <span className="text-purple-600 font-medium">
                    ("natural language processing" OR NLP) AND (sentiment OR emotion) AND (social media OR twitter)
                  </span>
                  <br />
                  NLP papers about sentiment analysis on social media
                </p>
              </div>
            </div>
          </div>
        </DialogContent>
      </Dialog>

    </div>
  )
}
