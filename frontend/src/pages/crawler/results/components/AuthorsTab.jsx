import { useMemo, useState } from 'react'
import { Loader2 } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { useToast } from '@/hooks/use-toast'
import { downloadTextFile } from '../utils'
import CopyUsageHelp from './CopyUsageHelp'

const deriveAffiliation = (author) => {
  if (!author) return ''
  if (author.affiliation) return author.affiliation
  if (author.primary_institution) return author.primary_institution
  if (author.primary_institution_name) return author.primary_institution_name
  if (author.institution) return author.institution
  if (Array.isArray(author.institutions) && author.institutions.length) {
    const first = author.institutions[0] || {}
    return first.display_name || first.name || ''
  }
  return ''
}

const buildAuthorUrl = (authorId) => {
  if (!authorId) return null
  const trimmed = String(authorId).trim()
  if (!trimmed) return null
  if (/^https?:\/\//i.test(trimmed)) return trimmed
  if (/^openalex\.org\//i.test(trimmed)) return `https://${trimmed}`
  return `https://openalex.org/${trimmed}`
}

export default function AuthorsTab({ authors, onOpenAuthor }) {
  const { toast } = useToast()
  const [includeLabels, setIncludeLabels] = useState(false)
  const [copying, setCopying] = useState(false)
  const [downloading, setDownloading] = useState(false)

  const authorEntries = useMemo(() => {
    return authors
      .map((author) => {
        const url = buildAuthorUrl(author?.author_id)
        if (!url) return null
        const affiliation = deriveAffiliation(author)
        const label = [author?.author_name, affiliation].filter(Boolean).join(' — ')
        return { url, label }
      })
      .filter(Boolean)
  }, [authors])

  const handleCopyAuthors = async () => {
    if (!authorEntries.length) {
      toast({
        title: 'No OpenAlex author URLs',
        description: 'Run a crawl that returns author identifiers first.',
        variant: 'destructive',
      })
      return
    }
    setCopying(true)
    try {
      const lines = authorEntries.map(({ url, label }) =>
        includeLabels && label ? `${label}: ${url}` : url
      )
      await navigator.clipboard.writeText(lines.join('\n'))
      toast({
        title: `Copied ${authorEntries.length} author profile${
          authorEntries.length === 1 ? '' : 's'
        }`,
        description: includeLabels
          ? 'Labels and URLs are ready to paste into NotebookLM or other tools.'
          : 'One OpenAlex URL per line is ready to paste.',
        variant: 'success',
      })
    } catch (err) {
      console.error(err)
      toast({
        title: 'Unable to copy author URLs',
        description: err?.message || 'Clipboard permission was denied.',
        variant: 'destructive',
      })
    } finally {
      setCopying(false)
    }
  }

  const handleDownloadAuthors = async () => {
    if (!authorEntries.length) {
      toast({
        title: 'No OpenAlex author URLs',
        description: 'Run a crawl that returns author identifiers first.',
        variant: 'destructive',
      })
      return
    }
    setDownloading(true)
    try {
      const lines = authorEntries.map(({ url, label }) =>
        includeLabels && label ? `${label}: ${url}` : url
      )
      downloadTextFile('author_links.txt', lines.join('\n'))
      toast({
        title: `Downloaded ${authorEntries.length} author link${
          authorEntries.length === 1 ? '' : 's'
        }`,
        description: 'Check your downloads folder for author_links.txt.',
      })
    } catch (err) {
      console.error(err)
      toast({
        title: 'Unable to download author URLs',
        description: err?.message || 'Something went wrong while creating the file.',
        variant: 'destructive',
      })
    } finally {
      setDownloading(false)
    }
  }

  return (
    <section className="space-y-6">
      <div className="rounded-3xl border border-gray-200 shadow-sm p-6">
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
          <h2 className="text-2xl font-semibold text-gray-900">Top authors</h2>
          {authors.length ? (
            <div className="flex flex-wrap items-center gap-3 text-xs text-gray-600">
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  checked={includeLabels}
                  onChange={(event) => setIncludeLabels(event.target.checked)}
                />
                Include labels (name + affiliation)
              </label>
              <div className="flex flex-wrap items-center gap-2">
                <div className="flex flex-wrap gap-2">
                  <Button
                    variant="outline"
                    className="rounded-full"
                    onClick={handleCopyAuthors}
                    disabled={copying}
                  >
                    {copying ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Copying…
                      </>
                    ) : (
                      'Copy author URLs'
                    )}
                  </Button>
                  <Button
                    variant="outline"
                    className="rounded-full"
                    onClick={handleDownloadAuthors}
                    disabled={downloading}
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
                <CopyUsageHelp contextLabel="author profile URLs and labels" tooltip="Copy URL usage" />
              </div>
            </div>
          ) : null}
        </div>
        {authors.length ? (
          <ul className="divide-y divide-gray-100">
            {authors.slice(0, 12).map((author) => {
              const initials = author.author_name
                .split(' ')
                .map((part) => part[0])
                .join('')
                .slice(0, 2)
                .toUpperCase()
              return (
                <li
                  key={author.author_id}
                  className="py-4 flex items-center justify-between cursor-pointer rounded-xl transition-colors hover:bg-gray-50"
                  onClick={() => onOpenAuthor?.(author)}
                  onKeyDown={(event) => {
                    if ((event.key === 'Enter' || event.key === ' ') && onOpenAuthor) {
                      event.preventDefault()
                      onOpenAuthor(author)
                    }
                  }}
                  tabIndex={onOpenAuthor ? 0 : -1}
                  role={onOpenAuthor ? 'button' : undefined}
                >
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-gray-100 flex items-center justify-center text-gray-600 font-semibold">
                      {initials || 'A'}
                    </div>
                    <div>
                      <p className="font-semibold text-gray-900">{author.author_name}</p>
                      <p className="text-xs text-gray-500 font-mono">{author.author_id}</p>
                    </div>
                  </div>
                  <div className="text-right text-sm text-gray-600">
                    <p>{author.paper_count} papers</p>
                    <p>{author.total_citations} citations</p>
                  </div>
                </li>
              )
            })}
          </ul>
        ) : (
          <p className="text-sm text-gray-500">No authors available yet.</p>
        )}
      </div>
    </section>
  )
}
