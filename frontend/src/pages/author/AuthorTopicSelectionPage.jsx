import { useCallback, useEffect, useMemo, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { Loader2, Search } from 'lucide-react'

import apiClient from '@/shared/api/client'
import { endpoints } from '@/shared/api/endpoints'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import Stepper from '@/components/Stepper'
import { saveSelectedAuthor } from './storage'

export default function AuthorTopicSelectionPage() {
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  const initialQuery = searchParams.get('author') || ''

  const [searchQuery, setSearchQuery] = useState(initialQuery)
  const [authors, setAuthors] = useState([])
  const [searching, setSearching] = useState(false)
  const [searchError, setSearchError] = useState(null)
  const [searchMeta, setSearchMeta] = useState(null)
  const [prefilledSearch, setPrefilledSearch] = useState(false)
  const [selectedAuthorId, setSelectedAuthorId] = useState(null)

  const selectedAuthor = useMemo(
    () => authors.find((author) => author.id === selectedAuthorId) || null,
    [authors, selectedAuthorId]
  )

  const runSearch = useCallback(
    async (termRaw) => {
      const query = (termRaw ?? searchQuery).trim()
      if (!query) return
      setSearchError(null)
      setSearching(true)
      setSelectedAuthorId(null)
      try {
        const { data, error } = await apiClient('POST', `${endpoints.authorTopicEvolution}/search`, {
          query,
          limit: 10,
          api_provider: 'openalex',
        })
        if (error) {
          setSearchError(error)
          setAuthors([])
          setSearchMeta(null)
        } else {
          setAuthors(data?.authors || [])
          setSearchMeta({
            total: data?.total_results ?? 0,
            query,
          })
        }
        setSearchParams((prev) => {
          const next = new URLSearchParams(prev)
          if (query) next.set('author', query)
          else next.delete('author')
          return next
        })
      } finally {
        setSearching(false)
      }
    },
    [searchQuery, setSearchParams]
  )

  useEffect(() => {
    if (initialQuery && !prefilledSearch) {
      setPrefilledSearch(true)
      runSearch(initialQuery)
    }
  }, [initialQuery, prefilledSearch, runSearch])

  const handleSearch = async (event) => {
    event?.preventDefault()
    await runSearch(searchQuery)
  }

  const handleContinue = () => {
    if (!selectedAuthor) return
    saveSelectedAuthor(selectedAuthor)
    navigate('/author-topic-evolution/configure')
  }

  return (
    <div className="min-h-[calc(100vh-160px)] bg-white">
      <div className="max-w-6xl mx-auto px-6 py-10">
        <Stepper
          steps={['Select author', 'Configure', 'Analyze', 'Results']}
          currentStep={1}
        />

        <div className="mt-6 mb-10 max-w-3xl space-y-3">
          <p className="text-sm uppercase tracking-[0.35em] text-gray-500">Step 1 · Select author</p>
          <h1 className="text-4xl font-bold text-gray-900">Choose the author you want to analyze</h1>
          <p className="text-lg text-gray-600">
            Search OpenAlex for matching researchers and select the identity you want to explore. You&apos;ll configure
            topic modeling options after this step.
          </p>
        </div>

        <div className="space-y-6">
          <AuthorSearchCard
            query={searchQuery}
            onChange={setSearchQuery}
            onSearch={handleSearch}
            loading={searching}
            error={searchError}
            meta={searchMeta}
          />

          <AuthorResultList
            authors={authors}
            loading={searching}
            selectedAuthorId={selectedAuthorId}
            onSelect={setSelectedAuthorId}
          />

          <div className="flex flex-col gap-3 border-t border-gray-100 pt-6 text-sm text-gray-500 md:flex-row md:items-center md:justify-between">
            <p>{selectedAuthor ? `Selected: ${selectedAuthor.name}` : 'Select an author to continue.'}</p>
            <Button
              className="rounded-full bg-gray-900 px-8 text-white hover:bg-gray-800 disabled:bg-gray-200 disabled:text-gray-500"
              onClick={handleContinue}
              disabled={!selectedAuthor || searching}
            >
              Continue to configuration
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}

function AuthorSearchCard({ query, onChange, onSearch, loading, error, meta }) {
  return (
    <Card className="border-none shadow-none px-0">
      <CardHeader className="pb-2">
        <CardTitle className="text-2xl text-gray-900">Search for an author</CardTitle>
        <p className="text-sm text-gray-500">
          Results come from OpenAlex. Enter a name, then select the author identity that matches your target researcher.
        </p>
      </CardHeader>
      <CardContent className="pt-4">
        <form
          onSubmit={onSearch}
          className="flex flex-col gap-4 md:flex-row"
        >
          <div className="flex-1">
            <label className="text-xs font-semibold uppercase tracking-wide text-gray-500">Author name</label>
            <Input
              placeholder="Ada Lovelace"
              value={query}
              onChange={(e) => onChange(e.target.value)}
              className="mt-1 rounded-2xl border-gray-200 px-4 py-3 text-base shadow-sm"
            />
          </div>
          <div className="md:w-40 flex items-end">
            <Button
              type="submit"
              className="w-full rounded-full bg-gray-900 text-white hover:bg-gray-800 disabled:bg-gray-200 disabled:text-gray-500"
              disabled={!query.trim() || loading}
            >
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Searching
                </>
              ) : (
                <>
                  <Search className="mr-2 h-4 w-4" />
                  Search
                </>
              )}
            </Button>
          </div>
        </form>
        {error && <p className="mt-3 rounded-2xl bg-red-50 px-4 py-3 text-sm text-red-700">{error}</p>}
        {!error && meta && (
          <p className="mt-3 text-sm text-gray-600">
            {meta.total} {meta.total === 1 ? 'author' : 'authors'} found for “{meta.query}”.
          </p>
        )}
      </CardContent>
    </Card>
  )
}

function AuthorResultList({ authors, loading, selectedAuthorId, onSelect }) {
  if (!authors.length) {
    return (
      <Card className="border-none shadow-none">
        <CardContent className="py-16 text-center text-sm text-gray-500">
          {loading ? 'Searching authors…' : 'Enter a name above to see matching authors.'}
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-3">
      {authors.map((author, index) => {
        const selected = selectedAuthorId === author.id
        return (
          <button
            key={author.id}
            onClick={() => onSelect(author.id)}
            className={`w-full border-b border-gray-200 pb-4 text-left transition-colors hover:bg-gray-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gray-300 ${
              selected ? 'bg-gray-50' : 'bg-white'
            }`}
          >
            <div className="flex items-start gap-4">
              <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full bg-gray-100 text-sm font-semibold text-gray-700">
                {index + 1}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex flex-wrap items-baseline gap-2">
                  <p className="text-lg font-semibold text-gray-900">{author.name}</p>
                  <p className="text-xs font-semibold uppercase tracking-[0.2em] text-gray-400">{author.id}</p>
                </div>
                <div className="mt-2 flex flex-wrap gap-4 text-sm text-gray-600">
                  <span>{author.works_count?.toLocaleString()} works</span>
                  <span>{author.cited_by_count?.toLocaleString()} citations</span>
                  {author.orcid && <span>ORCID {author.orcid}</span>}
                </div>
                {!!author.institutions?.length && (
                  <p className="mt-1 text-sm text-gray-500">{author.institutions.join(' • ')}</p>
                )}
                {selected && <p className="mt-2 text-xs font-semibold uppercase tracking-wide text-gray-500">Selected</p>}
              </div>
            </div>
          </button>
        )
      })}
    </div>
  )
}
