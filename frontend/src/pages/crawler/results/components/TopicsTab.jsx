import { useCallback, useMemo, useState } from 'react'
import { Loader2 } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { useToast } from '@/hooks/use-toast'
import apiClient from '@/shared/api/client'
import { endpoints } from '@/shared/api/endpoints'
import { downloadTextFile, getPreferredPaperUrl } from '../utils'

const TOPIC_COPY_PAGE_SIZE = 50

export default function TopicsTab({ topics, onOpenTopic, jobId }) {
  const { toast } = useToast()
  const [plainUrlsOnly, setPlainUrlsOnly] = useState(false)
  const [copying, setCopying] = useState(false)
  const [downloading, setDownloading] = useState(false)

  const topicCount = topics.length
  const hasTopics = topicCount > 0

  const fetchAllPapersForTopic = useCallback(
    async (topicId) => {
      if (!jobId || topicId === undefined || topicId === null) return []
      let page = 1
      let collected = []
      let total = 0
      while (true) {
        const res = await apiClient(
          'GET',
          `${endpoints.crawler}/jobs/${jobId}/topics/${topicId}/papers`,
          undefined,
          {
            query: {
              page,
              page_size: TOPIC_COPY_PAGE_SIZE,
            },
          }
        )
        if (res.error) {
          throw new Error(res.error)
        }
        const payload = res.data || {}
        const batch = Array.isArray(payload.papers) ? payload.papers : []
        total = payload.total ?? total ?? 0
        collected = collected.concat(batch)
        if (!batch.length || collected.length >= total) {
          break
        }
        page += 1
      }
      return collected
    },
    [jobId]
  )

  const buildTopicExportPayload = useCallback(async () => {
    const topicBlocks = []
    const allPlainUrls = []

    for (let idx = 0; idx < topics.length; idx += 1) {
      const topic = topics[idx]
      const topicId = topic?.topic_id
      const keywords = Array.isArray(topic?.top_words)
        ? topic.top_words.filter((word) => word && word.trim().length > 0)
        : []
      const keywordLine = keywords.length ? keywords.join(', ') : '(none)'

      let papers = []
      try {
        papers = await fetchAllPapersForTopic(topicId)
      } catch (err) {
        console.error('Failed to load topic papers', err)
        papers = []
      }

      let paperUrls = papers
        .map((paper) => getPreferredPaperUrl(paper))
        .filter((url) => typeof url === 'string' && url.length > 0)

      if (!paperUrls.length && Array.isArray(topic?.paper_ids)) {
        paperUrls = topic.paper_ids
          .map((id) => (id ? `https://openalex.org/${id}` : null))
          .filter(Boolean)
      }

      if (plainUrlsOnly) {
        allPlainUrls.push(...paperUrls)
      } else {
        const displayName =
          (topic?.topic_label && topic.topic_label.trim().length
            ? topic.topic_label
            : `Topic ${topicId ?? idx + 1}`) || `Topic ${idx + 1}`
        const lines = [
          `Topic ${idx + 1} – ${displayName}`,
          `Keywords: ${keywordLine}`,
        ]
        if (paperUrls.length) {
          lines.push('Papers:')
          paperUrls.forEach((url) => lines.push(`- ${url}`))
        } else {
          lines.push('Papers: (none)')
        }
        topicBlocks.push(lines.join('\n'))
      }
    }

    const totalLinks = plainUrlsOnly
      ? allPlainUrls.length
      : topicBlocks
          .map((block) => (block.match(/^- /gm) || []).length)
          .reduce((acc, count) => acc + count, 0)

    const payload = plainUrlsOnly ? allPlainUrls.join('\n') : topicBlocks.join('\n\n')
    return { payload, totalLinks }
  }, [fetchAllPapersForTopic, plainUrlsOnly, topics])

  const handleCopyTopics = useCallback(async () => {
    if (!jobId) {
      toast({
        title: 'Crawler job unavailable',
        description: 'Results must be loaded before copying topic data.',
        variant: 'destructive',
      })
      return
    }
    if (!hasTopics) {
      toast({
        title: 'No topics to copy',
        description: 'Run a crawl with topic modeling results first.',
        variant: 'destructive',
      })
      return
    }
    setCopying(true)
    try {
      const { payload, totalLinks } = await buildTopicExportPayload()
      if (!payload.trim()) {
        toast({
          title: 'Nothing to copy',
          description: 'Could not find URLs for any topics.',
          variant: 'destructive',
        })
        return
      }
      await navigator.clipboard.writeText(payload)
      toast({
        title: `Copied ${topicCount} topic${topicCount === 1 ? '' : 's'} (${totalLinks} link${
          totalLinks === 1 ? '' : 's'
        })`,
        description: plainUrlsOnly
          ? 'Plain URLs are ready to paste into NotebookLM or other tools.'
          : 'Topics, keywords, and links copied to clipboard.',
        variant: 'success',
      })
    } catch (err) {
      console.error(err)
      toast({
        title: 'Unable to copy topic data',
        description: err?.message || 'Clipboard permission was denied.',
        variant: 'destructive',
      })
    } finally {
      setCopying(false)
    }
  }, [buildTopicExportPayload, hasTopics, jobId, plainUrlsOnly, toast, topicCount])

  const handleDownloadTopics = useCallback(async () => {
    if (!jobId) {
      toast({
        title: 'Crawler job unavailable',
        description: 'Results must be loaded before downloading topic data.',
        variant: 'destructive',
      })
      return
    }
    if (!hasTopics) {
      toast({
        title: 'No topics to download',
        description: 'Run a crawl with topic modeling results first.',
        variant: 'destructive',
      })
      return
    }
    setDownloading(true)
    try {
      const { payload, totalLinks } = await buildTopicExportPayload()
      if (!payload.trim()) {
        toast({
          title: 'Nothing to download',
          description: 'Could not find URLs for any topics.',
          variant: 'destructive',
        })
        return
      }
      downloadTextFile(
        plainUrlsOnly ? 'topic_links.txt' : 'topic_export.txt',
        payload
      )
      toast({
        title: `Downloaded topic data (${totalLinks} link${totalLinks === 1 ? '' : 's'})`,
        description: 'Check your downloads folder for the TXT file.',
      })
    } catch (err) {
      console.error(err)
      toast({
        title: 'Unable to download topic data',
        description: err?.message || 'Something went wrong while generating the file.',
        variant: 'destructive',
      })
    } finally {
      setDownloading(false)
    }
  }, [buildTopicExportPayload, hasTopics, jobId, plainUrlsOnly, toast])

  const copyControls = useMemo(() => {
    if (!hasTopics) return null
    return (
      <div className="flex flex-wrap items-center gap-3">
        <label className="flex items-center gap-2 text-xs text-gray-600">
          <input
            type="checkbox"
            className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            checked={plainUrlsOnly}
            onChange={(event) => setPlainUrlsOnly(event.target.checked)}
          />
          Plain URLs only
        </label>
        <div className="flex gap-2 flex-wrap">
          <Button
            variant="outline"
            className="rounded-full"
            onClick={handleCopyTopics}
            disabled={!jobId || copying}
          >
            {copying ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Copying…
              </>
            ) : (
              'Copy topic data'
            )}
          </Button>
          <Button
            variant="outline"
            className="rounded-full"
            onClick={handleDownloadTopics}
            disabled={!jobId || downloading}
          >
            {downloading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Downloading…
              </>
            ) : (
              'Download TXT'
            )}
          </Button>
        </div>
      </div>
    )
  }, [copying, downloading, handleCopyTopics, handleDownloadTopics, hasTopics, jobId, plainUrlsOnly])

  return (
    <section className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-2xl font-semibold text-gray-900">Topics</h2>
        {copyControls}
      </div>
      {hasTopics ? (
        <>
          <p className="text-sm text-gray-500">
            Only topics with at least one paper that passed text processing appear below. Topics
            without enough qualifying abstracts are hidden automatically.
          </p>
          <p className="text-xs text-gray-400">
            Keyword chips below are the top words for each topic identified by the model.
          </p>
          <div className="grid gap-4 md:grid-cols-2">
          {topics.map((topic, index) => (
            <div
              key={topic.topic_id}
              className="rounded-3xl border border-gray-200 shadow-sm p-6 space-y-3"
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-lg font-semibold text-gray-900">Topic {index + 1}</p>
                  <p className="text-xs text-gray-400">Model topic ID: {topic.topic_id}</p>
                </div>
                <span className="text-xs text-gray-500">{topic.paper_count} papers</span>
              </div>
              <div className="flex flex-wrap gap-2" aria-label="Topic keywords">
                {(topic.top_words || []).slice(0, 8).map((word) => (
                  <span
                    key={`${topic.topic_id}-${word}`}
                    className="px-2 py-1 rounded-full bg-gray-100 text-xs text-gray-700"
                  >
                    {word}
                  </span>
                ))}
              </div>
              <div className="pt-2">
                <button
                  type="button"
                  onClick={() => onOpenTopic(topic)}
                  disabled={!jobId}
                  className="text-sm text-gray-600 flex items-center gap-1 hover:text-gray-900 disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  <span>View papers</span>
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    className="w-4 h-4"
                  >
                    <path d="M9 18l6-6-6-6" />
                  </svg>
                </button>
              </div>
            </div>
          ))}
          </div>
        </>
      ) : (
        <p className="text-sm text-gray-500">No topics available yet.</p>
      )}
    </section>
  )
}
