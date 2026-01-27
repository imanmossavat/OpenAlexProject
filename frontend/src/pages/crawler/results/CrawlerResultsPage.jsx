import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import {
  AlertCircle,
  Loader2,
  RefreshCcw,
  Settings as SettingsIcon,
} from 'lucide-react'

import apiClient from '@/shared/api/client'
import { endpoints } from '@/shared/api/endpoints'
import Stepper from '@/components/Stepper'
import { Button } from '@/components/ui/button'
import PaperDetailModal from '@/components/PaperDetailModal'
import { useToast } from '@/hooks/use-toast'
import useCrawlerPapers from './hooks/useCrawlerPapers'
import OverviewTab from './components/OverviewTab'
import TopPapersTab from './components/TopPapersTab'
import TopicsTab from './components/TopicsTab'
import AuthorsTab from './components/AuthorsTab'
import VenuesTab from './components/VenuesTab'
import CatalogSection from './components/CatalogSection'
import TopicDrawer from './components/TopicDrawer'
import EntityDrawer from './components/EntityDrawer'
import ProgressPanel from './components/ProgressPanel'
import CrawlerConfigDialog from './components/CrawlerConfigDialog'
import ZoteroExportModal from './components/ZoteroExportModal'
import { clearSession } from '@/shared/lib/session'
import { parseDate } from '@/shared/lib/time'

const steps = ['Keywords', 'Configuration', 'Run', 'Results']
const JOB_STORAGE_KEY = 'crawler_last_job_id'
const TOP_PAPERS_PAGE_SIZE = 6
const TOPIC_PAPERS_PAGE_SIZE = 20
const ENTITY_PAPERS_PAGE_SIZE = 20
const tabs = [
  { id: 'overview', label: 'Overview' },
  { id: 'top_papers', label: 'Top Papers' },
  { id: 'topics', label: 'Topics' },
  { id: 'authors', label: 'Authors' },
  { id: 'venues', label: 'Venues' },
  { id: 'all_papers', label: 'All Papers' },
]
export default function CrawlerResultsPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const jobParam = searchParams.get('job') || ''
  const initialJobId =
    jobParam ||
    (typeof window !== 'undefined' ? localStorage.getItem(JOB_STORAGE_KEY) || '' : '')
  const [jobId, setJobId] = useState(initialJobId)
  const [status, setStatus] = useState(null)
  const [results, setResults] = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)
  const [activeTab, setActiveTab] = useState('overview')
  const [topPapersPage, setTopPapersPage] = useState(1)
  const [detailPaper, setDetailPaper] = useState(null)
  const [detailModalOpen, setDetailModalOpen] = useState(false)
  const [detailLoading, setDetailLoading] = useState(false)
  const [detailError, setDetailError] = useState(null)
  const [topicViewer, setTopicViewer] = useState({ open: false, topic: null })
  const [topicDrawerVisible, setTopicDrawerVisible] = useState(false)
  const [topicDrawerAnimating, setTopicDrawerAnimating] = useState(false)
  const [topicPapers, setTopicPapers] = useState([])
  const [topicPage, setTopicPage] = useState(1)
  const [topicTotal, setTopicTotal] = useState(0)
  const [topicLoading, setTopicLoading] = useState(false)
  const [topicError, setTopicError] = useState(null)
  const [entityViewer, setEntityViewer] = useState({ open: false, type: null, id: null, label: '' })
  const [entityDrawerVisible, setEntityDrawerVisible] = useState(false)
  const [entityDrawerAnimating, setEntityDrawerAnimating] = useState(false)
  const [entityPapers, setEntityPapers] = useState([])
  const [entityPage, setEntityPage] = useState(1)
  const [entityTotal, setEntityTotal] = useState(0)
  const [entityLoading, setEntityLoading] = useState(false)
  const [entityError, setEntityError] = useState(null)
  const [centralityMetric, setCentralityMetric] = useState('centrality_in')
  const [selectedCatalogPaperIds, setSelectedCatalogPaperIds] = useState([])
  const [resumingIteration, setResumingIteration] = useState(false)
  const [configModalOpen, setConfigModalOpen] = useState(false)
  const { toast } = useToast()
  const [integrationStatus, setIntegrationStatus] = useState({ loading: true, zoteroConfigured: false })
  const [zoteroModalOpen, setZoteroModalOpen] = useState(false)
  const [zoteroCollections, setZoteroCollections] = useState([])
  const [zoteroCollectionsLoading, setZoteroCollectionsLoading] = useState(false)
  const [zoteroCollectionsError, setZoteroCollectionsError] = useState(null)
  const [zoteroExportSubmitting, setZoteroExportSubmitting] = useState(false)
  const [zoteroForm, setZoteroForm] = useState({
    selectedCollectionKey: '',
    newCollectionName: '',
    dedupe: true,
    tagsText: '',
  })
  const catalogEnabled = Boolean(jobId && status?.status === 'completed')
  const {
    papers: catalogPapers,
    total: catalogTotal,
    loading: catalogLoading,
    error: catalogError,
    page: catalogPage,
    pageSize: catalogPageSize,
    filters: catalogFilters,
  setPage: setCatalogPage,
  updateFilter: updateCatalogFilter,
  resetFilters: resetCatalogFilters,
  refresh: refreshCatalog,
    columnFilters,
    columnCustomFilters,
    columnOptions,
    applyColumnFilter,
    applyColumnCustomFilter,
    clearColumnFilter,
    clearAllColumnFilters,
    fetchColumnOptions: fetchCatalogColumnOptions,
    sortState: catalogSort,
    updateSortState: setCatalogSort,
  } = useCrawlerPapers({ jobId, pageSize: 25, enabled: catalogEnabled })
  const pollingRef = useRef(null)

  const stopPolling = useCallback(() => {
    if (pollingRef.current) {
      clearInterval(pollingRef.current)
      pollingRef.current = null
    }
  }, [])

  const fetchResults = useCallback(async (id) => {
    const res = await apiClient('GET', `${endpoints.crawlerJobs}/${id}/results`)
    if (res.error) {
      setError(res.error)
      return
    }
    setResults(res.data)
  }, [])

  const fetchStatus = useCallback(
    async (id) => {
      if (!id) return
      setLoading(true)
      const res = await apiClient('GET', `${endpoints.crawlerJobs}/${id}/status`)
      if (res.error) {
        setError(res.error)
        setLoading(false)
        return
      }
      setStatus(res.data)
      const jobStatus = res.data?.status
      if (jobStatus === 'completed') {
        stopPolling()
        await fetchResults(id)
        setStatus(res.data)
        setLoading(false)
        return
      } else if (jobStatus === 'failed') {
        stopPolling()
        setError(res.data?.error_message || 'Crawler job failed.')
        setStatus(res.data)
        setLoading(false)
        return
      }
      setLoading(false)
    },
    [fetchResults, stopPolling]
  )

  const startPolling = useCallback(
    (id) => {
      if (!id) return
      stopPolling()
      fetchStatus(id)
      pollingRef.current = setInterval(() => fetchStatus(id), 5000)
    },
    [fetchStatus, stopPolling]
  )

  useEffect(() => {
    if (jobParam) {
      setJobId(jobParam)
      try {
        localStorage.setItem(JOB_STORAGE_KEY, jobParam)
      } catch (e) {
        // ignore storage errors
      }
    }
  }, [jobParam])

  useEffect(() => {
    if (!jobId) return
    startPolling(jobId)
    return () => stopPolling()
  }, [jobId, startPolling, stopPolling])

  useEffect(() => {
    let cancelled = false
    const fetchIntegrationStatus = async () => {
      const res = await apiClient('GET', `${endpoints.settings}/integrations`)
      if (cancelled) return
      if (res.error) {
        setIntegrationStatus({ loading: false, zoteroConfigured: false })
        return
      }
      setIntegrationStatus({
        loading: false,
        zoteroConfigured: Boolean(res.data?.zotero?.configured),
      })
    }
    fetchIntegrationStatus()
    return () => {
      cancelled = true
    }
  }, [])

  useEffect(() => {
    if (results) setActiveTab('overview')
  }, [results])
  useEffect(() => {
    if (activeTab === 'top_papers') {
      setTopPapersPage(1)
    }
  }, [activeTab])

  const handleRefresh = () => {
    if (jobId) fetchStatus(jobId)
  }

  const handleCatalogSelectionChange = useCallback((ids = []) => {
    setSelectedCatalogPaperIds(Array.isArray(ids) ? ids : [])
  }, [])

  const manualIterationReady = status?.status === 'completed' && selectedCatalogPaperIds.length > 0

  const handleManualIteration = useCallback(async () => {
    if (!jobId || !selectedCatalogPaperIds.length) return
    const sanitizedPaperIds = Array.from(
      new Set(
        selectedCatalogPaperIds
          .map((value) => (typeof value === 'string' ? value.trim() : String(value || '')))
          .filter((value) => value.length > 0)
      )
    )
    if (!sanitizedPaperIds.length) return
    setResumingIteration(true)
    setError(null)
    try {
      const res = await apiClient('POST', `${endpoints.crawlerJobs}/${encodeURIComponent(jobId)}/resume`, {
        mode: 'manual',
        paper_ids: sanitizedPaperIds,
      })
      if (res.error) {
        setError(res.error)
        setResumingIteration(false)
        return
      }
      setResults(null)
      setActiveTab('overview')
      setSelectedCatalogPaperIds([])
      startPolling(jobId)
    } catch (err) {
      setError(err?.message || 'Unable to start manual iteration.')
    } finally {
      setResumingIteration(false)
    }
  }, [jobId, selectedCatalogPaperIds, startPolling])

  const fetchZoteroCollections = useCallback(async () => {
    setZoteroCollectionsLoading(true)
    setZoteroCollectionsError(null)
    const res = await apiClient('GET', `${endpoints.zotero}/collections`)
    if (res.error) {
      setZoteroCollections([])
      setZoteroCollectionsError(res.error)
    } else {
      setZoteroCollections(Array.isArray(res.data?.collections) ? res.data.collections : [])
    }
    setZoteroCollectionsLoading(false)
  }, [])

  const handleOpenZoteroExport = useCallback(async () => {
    if (!selectedCatalogPaperIds.length) {
      toast({
        title: 'No papers selected',
        description: 'Select at least one paper in the catalog before exporting.',
        variant: 'destructive',
      })
      return
    }
    if (integrationStatus.loading) {
      toast({ title: 'Please wait', description: 'Checking Zotero configuration…' })
      return
    }
    if (!integrationStatus.zoteroConfigured) {
      toast({
        title: 'Zotero not configured',
        description: 'Connect your Zotero account inside Settings → Integrations.',
        variant: 'destructive',
      })
      navigate('/settings/integrations?provider=zotero')
      return
    }
    setZoteroCollectionsError(null)
    setZoteroForm((prev) => ({ ...prev, selectedCollectionKey: '', newCollectionName: '' }))
    setZoteroModalOpen(true)
    fetchZoteroCollections()
  }, [selectedCatalogPaperIds, integrationStatus, toast, navigate, fetchZoteroCollections])

  const handleConfirmZoteroExport = useCallback(async () => {
    const WRITE_DENIED_PATTERN = /write access denied/i
    if (!jobId || !selectedCatalogPaperIds.length) {
      toast({
        title: 'No papers selected',
        description: 'Select at least one paper in the catalog before exporting.',
        variant: 'destructive',
      })
      return
    }
    const trimmedName = (zoteroForm.newCollectionName || '').trim()
    if (!zoteroForm.selectedCollectionKey && !trimmedName) {
      setZoteroCollectionsError('Select an existing collection or enter a new collection name.')
      return
    }
    setZoteroExportSubmitting(true)
    const payload = {
      paper_ids: selectedCatalogPaperIds,
      dedupe: zoteroForm.dedupe,
      tags: (zoteroForm.tagsText || '')
        .split(',')
        .map((tag) => tag.trim())
        .filter((value) => value.length > 0),
    }
    if (zoteroForm.selectedCollectionKey) {
      payload.collection_key = zoteroForm.selectedCollectionKey
    }
    if (!zoteroForm.selectedCollectionKey && trimmedName) {
      payload.collection_name = trimmedName
      payload.create_collection = true
    }
    const res = await apiClient(
      'POST',
      `${endpoints.zotero}/crawler/jobs/${encodeURIComponent(jobId)}/export`,
      payload
    )
    setZoteroExportSubmitting(false)
    if (res.error) {
      if (WRITE_DENIED_PATTERN.test(res.error || '')) {
        toast({
          title: 'Write access denied',
          description: 'Your Zotero API key is read-only. Update it in Settings → Integrations and try again.',
          variant: 'destructive',
        })
      }
      setZoteroCollectionsError(res.error)
      return
    }
    const data = res.data || {}
    const failedReasons = Object.values(data.failed_papers || {})
    if (
      WRITE_DENIED_PATTERN.test(data.error || '') ||
      failedReasons.some((reason) => WRITE_DENIED_PATTERN.test(String(reason || '')))
    ) {
      toast({
        title: 'Write access denied',
        description: 'Your Zotero API key is read-only. Update it in Settings → Integrations and try again.',
        variant: 'destructive',
      })
      setZoteroCollectionsError('Zotero rejected the export because the API key has read-only permissions.')
      return
    }
    toast({
      title: 'Export completed',
      description: `Created ${data.created || 0} item${(data.created || 0) === 1 ? '' : 's'}${
        data.skipped ? `, ${data.skipped} skipped` : ''
      }${data.failed ? `, ${data.failed} failed` : ''}.`,
    })
    setZoteroModalOpen(false)
    setZoteroForm({
      selectedCollectionKey: '',
      newCollectionName: '',
      dedupe: true,
      tagsText: '',
    })
  }, [jobId, selectedCatalogPaperIds, zoteroForm, toast])

  const handleFinishAndReset = useCallback(() => {
    try {
      localStorage.removeItem(JOB_STORAGE_KEY)
    } catch (e) {
      // ignore storage errors
    }
    try {
      clearSession()
    } catch (e) {
      // ignore storage errors
    }
    setJobId('')
    setResults(null)
    setStatus(null)
    navigate('/')
  }, [navigate])

  const progress = useMemo(() => {
    if (!status) return null
    const iterationsCompleted = Math.max(
      0,
      status.iterations_completed ?? status.current_iteration ?? 0
    )
    const iterationsTotalCandidate =
      status.max_iterations ??
      status.iterations_total ??
      (iterationsCompleted > 0 ? iterationsCompleted : 0)
    const iterationsTotal = Math.max(iterationsTotalCandidate, iterationsCompleted)
    const iterationsRemaining =
      status.iterations_remaining ?? Math.max(iterationsTotal - iterationsCompleted, 0)
    let percent = iterationsTotal > 0 ? Math.round((iterationsCompleted / iterationsTotal) * 100) : 0
    if (status.status === 'completed' && percent < 100) percent = 100
    percent = Math.min(100, Math.max(0, percent))

    const startedAt = parseDate(status.started_at)
    const lastUpdateRaw = status.last_progress_at || status.completed_at
    const lastUpdate = parseDate(lastUpdateRaw) || startedAt

    return {
      status: status.status,
      percent,
      iterationsCompleted,
      iterationsTotal,
      iterationsRemaining,
      papersCollected: status.papers_collected ?? 0,
      seedPapers: status.seed_papers ?? 0,
      citations: status.citations_collected ?? 0,
      references: status.references_collected ?? 0,
      startedAt,
      lastUpdate,
    }
  }, [status])

  const networkOverview = useMemo(() => {
    if (!results?.network_overview) return []
    const n = results.network_overview
    return [
      { label: 'Total nodes', value: n.total_nodes },
      { label: 'Total edges', value: n.total_edges },
      { label: 'Papers collected', value: n.total_papers },
      { label: 'Iterations', value: n.total_iterations },
      { label: 'Topics', value: n.total_topics },
      { label: 'Retracted papers', value: n.retracted_papers },
    ]
  }, [results])

  const circleMetrics = useMemo(() => {
    if (!results?.network_overview) return []
    const n = results.network_overview
    return [
      { label: 'Papers (Nodes)', value: n.paper_nodes ?? n.total_papers ?? 0 },
      { label: 'Citations (Edges)', value: n.total_edges ?? 0 },
    ]
  }, [results])

  const temporalData = useMemo(() => {
    if (!results?.temporal_distribution?.length) return []
    const baseYears = new Set(Array.from({ length: 10 }, (_, i) => 2015 + i))
    const distribution = results.temporal_distribution.reduce((acc, item) => {
      if (item?.year != null) {
        acc[item.year] = item.paper_count
        baseYears.add(item.year)
      }
      return acc
    }, {})
    return Array.from(baseYears)
      .sort((a, b) => a - b)
      .map((year) => ({
        year,
        paper_count: distribution[year] ?? 0,
      }))
  }, [results])

  const sortedTopPapers = useMemo(() => {
    const papers = results?.top_papers ?? []
    if (!papers.length) return []
    return [...papers].sort((a, b) => {
      const metricsA = a.centrality_metrics || {}
      const metricsB = b.centrality_metrics || {}
      const valA =
        typeof metricsA?.[centralityMetric] === 'number'
          ? metricsA[centralityMetric]
          : typeof a.centrality_score === 'number'
          ? a.centrality_score
          : 0
      const valB =
        typeof metricsB?.[centralityMetric] === 'number'
          ? metricsB[centralityMetric]
          : typeof b.centrality_score === 'number'
          ? b.centrality_score
          : 0
      return Number(valB) - Number(valA)
    })
  }, [results?.top_papers, centralityMetric])

  const topics = results?.topics ?? []
  const topicMaxPage = topicTotal > 0 ? Math.ceil(topicTotal / TOPIC_PAPERS_PAGE_SIZE) : 1
  const topAuthors = results?.top_authors ?? []
  const topVenues = results?.top_venues ?? []
  const entityMaxPage = entityTotal > 0 ? Math.ceil(entityTotal / ENTITY_PAPERS_PAGE_SIZE) : 1
  const totalTopPaperPages = Math.max(
    1,
    Math.ceil(sortedTopPapers.length / TOP_PAPERS_PAGE_SIZE)
  )
  const configSnapshot = results?.config_snapshot || null

  const openPaperDetails = async (paper, options = {}) => {
    const { skipFetch = false } = options
    if (!paper?.paper_id) return
    const fallback = {
      paper_id: paper.paper_id,
      title: paper.title || paper.paper_id,
      abstract: paper.abstract || null,
      authors: Array.isArray(paper.authors) ? paper.authors : [],
      institutions: paper.institutions || [],
      year: paper.year ?? null,
      venue: paper.venue || null,
      doi: paper.doi || null,
      url: paper.url || `https://openalex.org/${paper.paper_id}`,
      cited_by_count:
        typeof paper.citation_count === 'number' ? paper.citation_count : paper.cited_by_count ?? null,
      references_count:
        typeof paper.references_count === 'number' ? paper.references_count : null,
    }
    setDetailPaper(fallback)
    setDetailError(null)
    setDetailLoading(!skipFetch)
    setDetailModalOpen(true)

    if (skipFetch) {
      return
    }

    const res = await apiClient(
      'GET',
      `${endpoints.papers}/${encodeURIComponent(paper.paper_id)}`
    )
    setDetailLoading(false)
    if (res.error) {
      setDetailError(res.error)
      return
    }
    if (res.data) {
      setDetailPaper(res.data)
    }
  }

  const closePaperDetails = () => {
    setDetailModalOpen(false)
    setDetailPaper(null)
    setDetailError(null)
    setDetailLoading(false)
  }

  const fetchTopicPapers = useCallback(
    async (topicId, requestedPage = 1) => {
      if (!jobId || topicId === undefined || topicId === null) return
      setTopicLoading(true)
      setTopicError(null)
      const res = await apiClient(
        'GET',
        `${endpoints.crawler}/jobs/${jobId}/topics/${topicId}/papers`,
        undefined,
        {
          query: {
            page: requestedPage,
            page_size: TOPIC_PAPERS_PAGE_SIZE,
          },
        }
      )
      if (res.error) {
        setTopicError(res.error)
        setTopicPapers([])
        setTopicTotal(0)
        setTopicLoading(false)
        return
      }
      const payload = res.data || {}
      setTopicPapers(Array.isArray(payload.papers) ? payload.papers : [])
      setTopicPage(payload.page || requestedPage)
      setTopicTotal(payload.total ?? 0)
      setTopicLoading(false)
    },
    [jobId]
  )

  const fetchEntityPapers = useCallback(
    async (entityType, entityId, requestedPage = 1) => {
      if (!jobId || !entityType || !entityId) return
      setEntityLoading(true)
      setEntityError(null)
      const resource = entityType === 'author' ? 'authors' : 'venues'
      const res = await apiClient(
        'GET',
        `${endpoints.crawler}/jobs/${jobId}/${resource}/${encodeURIComponent(entityId)}/papers`,
        undefined,
        {
          query: {
            page: requestedPage,
            page_size: ENTITY_PAPERS_PAGE_SIZE,
          },
        }
      )
      if (res.error) {
        setEntityError(res.error)
        setEntityPapers([])
        setEntityTotal(0)
        setEntityLoading(false)
        return
      }
      const payload = res.data || {}
      setEntityPapers(Array.isArray(payload.papers) ? payload.papers : [])
      setEntityPage(payload.page || requestedPage)
      setEntityTotal(payload.total ?? 0)
      setEntityLoading(false)
    },
    [jobId]
  )

  const openTopicModal = (topic) => {
    if (!jobId || !topic) return
    setTopicViewer({ open: true, topic })
    fetchTopicPapers(topic.topic_id, 1)
  }

  const closeTopicModal = () => {
    setTopicViewer((prev) => ({ ...prev, open: false }))
  }

  useEffect(() => {
    let timeoutId
    if (topicViewer.open) {
      setTopicDrawerVisible(true)
      requestAnimationFrame(() => {
        requestAnimationFrame(() => setTopicDrawerAnimating(true))
      })
    } else if (topicDrawerVisible) {
      setTopicDrawerAnimating(false)
      timeoutId = setTimeout(() => {
        setTopicDrawerVisible(false)
        setTopicViewer({ open: false, topic: null })
        setTopicPapers([])
        setTopicPage(1)
        setTopicTotal(0)
        setTopicError(null)
      }, 300)
    }
    return () => {
      if (timeoutId) clearTimeout(timeoutId)
    }
  }, [topicViewer.open, topicDrawerVisible])

  useEffect(() => {
    let timeoutId
    if (entityViewer.open) {
      setEntityDrawerVisible(true)
      requestAnimationFrame(() => {
        requestAnimationFrame(() => setEntityDrawerAnimating(true))
      })
    } else if (entityDrawerVisible) {
      setEntityDrawerAnimating(false)
      timeoutId = setTimeout(() => {
        setEntityDrawerVisible(false)
        setEntityViewer({ open: false, type: null, id: null, label: '' })
        setEntityPapers([])
        setEntityPage(1)
        setEntityTotal(0)
        setEntityError(null)
      }, 300)
    }
    return () => {
      if (timeoutId) clearTimeout(timeoutId)
    }
  }, [entityViewer.open, entityDrawerVisible])

  const handleTopicPageChange = (direction) => {
    if (!topicViewer.topic) return
    const nextPage = topicPage + direction
    if (nextPage < 1) return
    const maxPage = topicTotal > 0 ? Math.ceil(topicTotal / TOPIC_PAPERS_PAGE_SIZE) : 1
    if (nextPage > maxPage) return
    fetchTopicPapers(topicViewer.topic.topic_id, nextPage)
  }

  const openAuthorDrawer = (author) => {
    if (!jobId || !author?.author_id) return
    setEntityViewer({
      open: true,
      type: 'author',
      id: author.author_id,
      label: author.author_name || author.author_id,
    })
    fetchEntityPapers('author', author.author_id, 1)
  }

  const openVenueDrawer = (venue) => {
    if (!jobId || !venue?.venue) return
    setEntityViewer({
      open: true,
      type: 'venue',
      id: venue.venue,
      label: venue.venue || 'Venue',
    })
    fetchEntityPapers('venue', venue.venue, 1)
  }

  const closeEntityDrawer = () => {
    setEntityViewer((prev) => ({ ...prev, open: false }))
  }

  const handleEntityPageChange = (direction) => {
    if (!entityViewer.type || !entityViewer.id) return
    const nextPage = entityPage + direction
    if (nextPage < 1) return
    if (entityTotal > 0 && nextPage > entityMaxPage) return
    fetchEntityPapers(entityViewer.type, entityViewer.id, nextPage)
  }
  const showProgressPanel = progress && (status?.status === 'running' || status?.status === 'saving')

  const stepperStep = status?.status === 'running' || status?.status === 'saving' ? 3 : 4

  return (
    <div className="min-h-[calc(100vh-160px)] bg-white">
      <div className="max-w-6xl mx-auto px-6 py-12 space-y-8">
        <Stepper steps={steps} currentStep={stepperStep} />

        <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
          <div className="flex flex-col gap-3">
            <p className="text-xs uppercase tracking-[0.4em] text-gray-500">Crawler workflow</p>
            <div className="flex items-center gap-3 flex-wrap">
              <h1 className="text-4xl font-bold text-gray-900">Crawler results</h1>
              {configSnapshot ? (
                <button
                  type="button"
                  onClick={() => setConfigModalOpen(true)}
                  title="View configuration"
                  className="rounded-full w-12 h-12 text-gray-700 hover:text-gray-900 bg-transparent flex items-center justify-center transition"
                >
                  <SettingsIcon className="w-7 h-7" />
                </button>
              ) : null}
            </div>
            <p className="text-gray-600 text-lg">
              Track the crawler job status and explore the resulting network, top papers, topics, and influential authors.
            </p>
          </div>
          {status?.status === 'completed' ? (
            <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
              <Button
                type="button"
                size="sm"
                variant="outline"
                className="rounded-full px-4 py-2"
                onClick={handleManualIteration}
                disabled={!manualIterationReady || resumingIteration}
              >
                {resumingIteration ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : null}
                Run manual iteration
                {selectedCatalogPaperIds.length
                  ? ` (${selectedCatalogPaperIds.length})`
                  : ''}
              </Button>
              {results ? (
                <Button
                  type="button"
                  size="sm"
                  className="rounded-full bg-gray-900 text-white hover:bg-gray-800 px-4 py-2"
                  onClick={handleFinishAndReset}
                >
                  Finish and reset
                </Button>
              ) : null}
            </div>
          ) : null}
        </div>

        {!jobId ? (
          <div className="rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-red-700 flex gap-2 items-start">
            <AlertCircle className="w-4 h-4 mt-0.5" />
            <div>No job provided. Start a crawler run first.</div>
          </div>
        ) : null}

        {error ? (
          <div className="rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-red-700 flex gap-2 items-start">
            <AlertCircle className="w-4 h-4 mt-0.5" />
            <div>{error}</div>
          </div>
        ) : null}

        {showProgressPanel ? <ProgressPanel progress={progress} /> : null}

        {!showProgressPanel && (status?.status === 'running' || status?.status === 'saving') ? (
          <div className="rounded-3xl border border-dashed border-gray-300 p-8 text-center text-gray-600">
            <div className="flex justify-center mb-3">
              <Loader2 className="w-5 h-5 animate-spin text-gray-500" />
            </div>
            Crawler is {status?.status === 'saving' ? 'saving results' : 'running'}. Results will appear automatically once it completes.
          </div>
        ) : status?.status === 'completed' && !results ? (
          <div className="rounded-3xl border border-dashed border-gray-300 p-8 text-center text-gray-600 space-y-3">
            <p>Results are still processing. Click refresh to check again.</p>
            <Button
              variant="outline"
              className="rounded-full"
              onClick={handleRefresh}
              disabled={loading}
            >
              {loading ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <RefreshCcw className="w-4 h-4 mr-2" />}
              Refresh
            </Button>
          </div>
        ) : results ? (
          <>
            <div className="border-b border-gray-200">
              <div className="flex gap-6">
                {tabs.map((tab) => (
                  <button
                    key={tab.id}
                    type="button"
                    className={`py-3 text-sm font-medium border-b-2 transition-colors ${
                      activeTab === tab.id
                        ? 'border-blue-600 text-blue-700'
                        : 'border-transparent text-gray-500 hover:text-gray-900'
                    }`}
                    onClick={() => setActiveTab(tab.id)}
                  >
                    {tab.label}
                  </button>
                ))}
              </div>
            </div>

            <div className="space-y-8">
              {activeTab === 'overview' && (
                <OverviewTab
                  networkOverview={networkOverview}
                  circleMetrics={circleMetrics}
                  temporalData={temporalData}
                />
              )}

              {activeTab === 'top_papers' && (
                <TopPapersTab
                  papers={sortedTopPapers}
                  currentPage={topPapersPage}
                  totalPages={totalTopPaperPages}
                  pageSize={TOP_PAPERS_PAGE_SIZE}
                  onPageChange={(nextPage) =>
                    setTopPapersPage((prev) => {
                      if (Number.isNaN(nextPage)) return prev
                      if (nextPage < 1) return 1
                      if (nextPage > totalTopPaperPages) return totalTopPaperPages
                      return nextPage
                    })
                  }
                  onSelectPaper={openPaperDetails}
                  centralityMetric={centralityMetric}
                  onCentralityMetricChange={setCentralityMetric}
                />
              )}

              {activeTab === 'topics' && (
                <TopicsTab topics={topics} onOpenTopic={openTopicModal} jobId={jobId} />
              )}

              {activeTab === 'authors' && <AuthorsTab authors={topAuthors} onOpenAuthor={openAuthorDrawer} />}

              {activeTab === 'venues' && <VenuesTab venues={topVenues} onOpenVenue={openVenueDrawer} />}

              {activeTab === 'all_papers' && (
                <CatalogSection
                  jobId={jobId}
                  topics={topics}
                  catalogEnabled={catalogEnabled}
                  catalogLoading={catalogLoading}
                  catalogError={catalogError}
                  catalogPapers={catalogPapers}
                  catalogTotal={catalogTotal}
                  catalogPage={catalogPage}
                  setCatalogPage={setCatalogPage}
                  catalogPageSize={catalogPageSize}
                  catalogFilters={catalogFilters}
                  updateCatalogFilter={updateCatalogFilter}
                  refreshCatalog={refreshCatalog}
                  catalogSort={catalogSort}
                  setCatalogSort={setCatalogSort}
                  columnFilters={columnFilters}
                  columnOptions={columnOptions}
                  columnCustomFilters={columnCustomFilters}
                  applyColumnFilter={applyColumnFilter}
                  applyColumnCustomFilter={applyColumnCustomFilter}
                  clearColumnFilter={clearColumnFilter}
                  clearAllColumnFilters={clearAllColumnFilters}
                  fetchCatalogColumnOptions={fetchCatalogColumnOptions}
                  onOpenPaperDetails={openPaperDetails}
                  onSelectionChange={handleCatalogSelectionChange}
                  onExportSelected={handleOpenZoteroExport}
                  exportingSelection={zoteroExportSubmitting}
                  exportDisabled={integrationStatus.loading}
                  exportDisabledReason={
                    integrationStatus.loading || integrationStatus.zoteroConfigured
                      ? ''
                      : 'Connect Zotero in Settings → Integrations to enable exports.'
                  }
                />
              )}
            </div>
          </>
        ) : status?.status === 'running' || status?.status === 'saving' ? null : (
          <div className="rounded-3xl border border-dashed border-gray-300 p-8 text-center text-gray-600">
            Start a crawler job to see results.
          </div>
        )}
      </div>
      <TopicDrawer
        visible={topicDrawerVisible}
        animating={topicDrawerAnimating}
        topic={topicViewer.topic}
        topicError={topicError}
        topicLoading={topicLoading}
        topicPapers={topicPapers}
        topicPage={topicPage}
        topicTotal={topicTotal}
        pageSize={TOPIC_PAPERS_PAGE_SIZE}
        onClose={closeTopicModal}
        onPreviousPage={() => handleTopicPageChange(-1)}
        onNextPage={() => handleTopicPageChange(1)}
        onSelectPaper={(paper) => openPaperDetails(paper, { skipFetch: true })}
        canGoPrevious={!topicLoading && topicPage > 1}
        canGoNext={!topicLoading && topicTotal > 0 && topicPage < topicMaxPage}
      />

      <EntityDrawer
        visible={entityDrawerVisible}
        animating={entityDrawerAnimating}
        title={entityViewer.type === 'venue' ? 'Venue' : 'Author'}
        subtitle={entityViewer.label || entityViewer.id || ''}
        error={entityError}
        loading={entityLoading}
        papers={entityPapers}
        page={entityPage}
        total={entityTotal}
        pageSize={ENTITY_PAPERS_PAGE_SIZE}
        onClose={closeEntityDrawer}
        onPreviousPage={() => handleEntityPageChange(-1)}
        onNextPage={() => handleEntityPageChange(1)}
        onSelectPaper={(paper) => openPaperDetails(paper, { skipFetch: true })}
        canGoPrevious={!entityLoading && entityPage > 1}
        canGoNext={!entityLoading && entityTotal > 0 && entityPage < entityMaxPage}
      />

      <ZoteroExportModal
        open={zoteroModalOpen}
        onClose={() => {
          setZoteroModalOpen(false)
          setZoteroCollectionsError(null)
        }}
        collections={zoteroCollections}
        loadingCollections={zoteroCollectionsLoading}
        collectionsError={zoteroCollectionsError}
        onRetryCollections={fetchZoteroCollections}
        onOpenSettings={() => navigate('/settings/integrations?provider=zotero')}
        selectedCollectionKey={zoteroForm.selectedCollectionKey}
        onSelectCollection={(key) =>
          setZoteroForm((prev) => ({ ...prev, selectedCollectionKey: key, newCollectionName: '' }))
        }
        newCollectionName={zoteroForm.newCollectionName}
        onNewCollectionNameChange={(value) =>
          setZoteroForm((prev) => ({ ...prev, newCollectionName: value, selectedCollectionKey: '' }))
        }
        dedupeEnabled={zoteroForm.dedupe}
        onToggleDedupe={(checked) => setZoteroForm((prev) => ({ ...prev, dedupe: Boolean(checked) }))}
        tagsText={zoteroForm.tagsText}
        onTagsTextChange={(value) => setZoteroForm((prev) => ({ ...prev, tagsText: value }))}
        submitting={zoteroExportSubmitting}
        onConfirm={handleConfirmZoteroExport}
      />

      <PaperDetailModal
        paper={detailPaper}
        isOpen={detailModalOpen && !!detailPaper}
        onClose={closePaperDetails}
        loading={detailLoading}
        error={detailError}
      />
      <CrawlerConfigDialog
        open={configModalOpen}
        onOpenChange={setConfigModalOpen}
        config={configSnapshot}
        iterations={results?.network_overview?.total_iterations}
      />
    </div>
  )
}
