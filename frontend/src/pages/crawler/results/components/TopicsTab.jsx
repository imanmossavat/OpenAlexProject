import { useCallback, useMemo, useState } from 'react'
import { Loader2 } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { useToast } from '@/hooks/use-toast'
import { downloadTextFile } from '../utils'
import CopyUsageHelp from './CopyUsageHelp'
const EXPORT_MODES = {
  structured: 'structured',
  plain: 'plain',
  llm: 'llm',
}

const LLM_SUMMARY_PROMPT = `You are analyzing topic-model output from an academic crawler.

Each topic block below contains:
- A topic name
- Porter-stemmed keywords (so some words look shortened, e.g., "observ" = "observations")
- A list of paper links (mostly DOI or OpenAlex URLs)

Task: For every topic, produce a structured analysis with the following sections:

1) Theme in everyday language (1-2 sentences).
2) Keywords unpacked: infer un-stemmed forms where possible and explain the shared concepts (focus on meaning rather than listing every variant).
3) Evidence example: mention at least one linked paper as an example. If you can resolve a title from the link, cite it by title; otherwise label it by position (e.g., "first paper").
4) Cross-topic notes: relationships, overlaps, or contrasts with other topics in this set.
5) Research directions: brief suggestions for synthesis, follow-up queries, or ways to validate or interpret the topics.

After all topics, write a short overall takeaway summarizing what this topic set collectively suggests.

Guidelines:
- Do not invent paper titles, results, or claims.
- Keep each topic concise and proportional to the amount of information available; do not pad weak topics.
- Use clear headings per topic.
- If a topic appears incoherent, duplicated, or dominated by preprocessing artifacts, say so and explain why.

Now analyze the following topics:`

const buildUrlFromLinkEntry = (entry) => {
  if (!entry) return null
  if (entry.doi && typeof entry.doi === 'string' && entry.doi.trim().length) {
    return `https://doi.org/${entry.doi.trim()}`
  }
  const directUrl =
    typeof entry.url === 'string' && entry.url.trim().length ? entry.url.trim() : null
  if (directUrl) return directUrl
  if (entry.paper_id) return `https://openalex.org/${entry.paper_id}`
  return null
}

const getTopicLinkUrls = (topic) => {
  if (Array.isArray(topic?.paper_links) && topic.paper_links.length) {
    return topic.paper_links.map((entry) => buildUrlFromLinkEntry(entry)).filter(Boolean)
  }
  if (Array.isArray(topic?.paper_ids)) {
    return topic.paper_ids
      .map((id) => (typeof id === 'string' && id.trim().length ? `https://openalex.org/${id}` : null))
      .filter(Boolean)
  }
  return []
}

export default function TopicsTab({ topics, onOpenTopic, jobId }) {
  const { toast } = useToast()
  const [exportMode, setExportMode] = useState(EXPORT_MODES.structured)
  const [copying, setCopying] = useState(false)
  const [downloading, setDownloading] = useState(false)

  const plainUrlsOnly = exportMode === EXPORT_MODES.plain
  const includeLlmPrompt = exportMode === EXPORT_MODES.llm

  const topicCount = topics.length
  const hasTopics = topicCount > 0
  const topicExportHelp = useMemo(
    () => [
      {
        title: 'Include keywords & URLs',
        content:
          'Default option with topic titles, stemmed keywords, and paper links for manual review, planning slides, or curation.',
      },
      {
        title: 'Plain URLs only',
        content:
          'Strips everything except links. Ideal for NotebookLM imports, spreadsheets, or sharing DOI lists with collaborators.',
      },
      {
        title: 'GPT-ready summary prompt',
        content:
          'Prepends an LLM instruction so you can paste the block into GPT/NotebookLM and get immediate explanations of each topic.',
      },
    ],
    []
  )

  const buildTopicExportPayload = useCallback(() => {
    const topicBlocks = []
    const allPlainUrls = []

    for (let idx = 0; idx < topics.length; idx += 1) {
      const topic = topics[idx]
      const topicId = topic?.topic_id
      const keywords = Array.isArray(topic?.top_words)
        ? topic.top_words.filter((word) => word && word.trim().length > 0)
        : []
      const keywordLine = keywords.length ? keywords.join(', ') : '(none)'

      const paperUrls = getTopicLinkUrls(topic)

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

    if (plainUrlsOnly) {
      return { payload: allPlainUrls.join('\n'), totalLinks }
    }

    const blockPayload = topicBlocks.join('\n\n')
    const payload = includeLlmPrompt
      ? `${LLM_SUMMARY_PROMPT.trim()}\n\n${blockPayload}`
      : blockPayload
    return { payload, totalLinks }
  }, [includeLlmPrompt, plainUrlsOnly, topics])

  const handleCopyTopics = useCallback(async () => {
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
      const { payload, totalLinks } = buildTopicExportPayload()
      if (!payload.trim()) {
        toast({
          title: 'Nothing to copy',
          description: 'Could not find URLs for any topics.',
          variant: 'destructive',
        })
        return
      }
      await navigator.clipboard.writeText(payload)
      let description = 'Topics, keywords, and links copied to clipboard.'
      if (plainUrlsOnly) {
        description = 'Plain URLs are ready to paste into NotebookLM or other tools.'
      } else if (includeLlmPrompt) {
        description = 'Prompt + topics copied. Paste into GPT/NotebookLM for instant summaries.'
      }
      toast({
        title: `Copied ${topicCount} topic${topicCount === 1 ? '' : 's'} (${totalLinks} link${
          totalLinks === 1 ? '' : 's'
        })`,
        description,
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
  }, [
    buildTopicExportPayload,
    hasTopics,
    includeLlmPrompt,
    plainUrlsOnly,
    toast,
    topicCount,
  ])

  const handleDownloadTopics = useCallback(async () => {
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
      const { payload, totalLinks } = buildTopicExportPayload()
      if (!payload.trim()) {
        toast({
          title: 'Nothing to download',
          description: 'Could not find URLs for any topics.',
          variant: 'destructive',
        })
        return
      }
      const fileName =
        exportMode === EXPORT_MODES.plain
          ? 'topic_links.txt'
          : exportMode === EXPORT_MODES.llm
          ? 'topic_llm_summary.txt'
          : 'topic_export.txt'
      downloadTextFile(fileName, payload)
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
  }, [buildTopicExportPayload, exportMode, hasTopics, plainUrlsOnly, toast])

  const copyControls = useMemo(() => {
    if (!hasTopics) return null
    const copyContext = (() => {
      if (plainUrlsOnly) return 'topic link lists (one URL per paper)'
      if (includeLlmPrompt) return 'topics with keywords, URLs, and an LLM prompt'
      return 'topics with keywords and URLs'
    })()
    return (
      <div className="flex flex-wrap items-center gap-3">
        <fieldset className="flex flex-wrap gap-3 text-xs text-gray-600">
          <legend className="sr-only">Topic export format</legend>
          <label className="flex items-center gap-2">
            <input
              type="radio"
              name="topic-export-format"
              className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              checked={exportMode === EXPORT_MODES.structured}
              onChange={() => setExportMode(EXPORT_MODES.structured)}
            />
            Include keywords & URLs
          </label>
          <label className="flex items-center gap-2">
            <input
              type="radio"
              name="topic-export-format"
              className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              checked={exportMode === EXPORT_MODES.plain}
              onChange={() => setExportMode(EXPORT_MODES.plain)}
            />
            Plain URLs only
          </label>
          <label className="flex items-center gap-2">
            <input
              type="radio"
              name="topic-export-format"
              className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              checked={exportMode === EXPORT_MODES.llm}
              onChange={() => setExportMode(EXPORT_MODES.llm)}
            />
            GPT-ready summary prompt
          </label>
        </fieldset>
        <div className="flex flex-wrap items-center gap-2">
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
          <CopyUsageHelp
            contextLabel={copyContext}
            tooltip="Copy URL usage"
            descriptionOverride="Choose a topic export format, then copy or download to keep analyzing in NotebookLM, GPT, or spreadsheets."
            extraSections={topicExportHelp}
            hideDefaultExamples
          />
        </div>
      </div>
    )
  }, [
    copying,
    downloading,
    exportMode,
    handleCopyTopics,
    handleDownloadTopics,
    hasTopics,
    includeLlmPrompt,
    jobId,
    plainUrlsOnly,
    topicExportHelp,
  ])

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
            Keyword chips below are the top words for each topic (shown after Porter stemming/tokenization, so some words appear shortened).
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
