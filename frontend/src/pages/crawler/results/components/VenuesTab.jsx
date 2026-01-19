import { useMemo, useState } from 'react'
import { Loader2 } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { useToast } from '@/hooks/use-toast'
import { downloadTextFile } from '../utils'
import CopyUsageHelp from './CopyUsageHelp'

const buildVenueUrl = (venue) => {
  if (!venue) return null
  const candidate = venue.venue_id || venue.venue || ''
  const trimmed = String(candidate).trim()
  if (!trimmed) return null
  if (/^https?:\/\//i.test(trimmed)) return trimmed
  if (/^openalex\.org\//i.test(trimmed)) return `https://${trimmed}`
  if (/^[Vv]\d+/i.test(trimmed)) return `https://openalex.org/${trimmed.toUpperCase()}`
  return null
}

const describeVenue = (venue) => (venue?.venue ? venue.venue : '')

export default function VenuesTab({ venues, onOpenVenue }) {
  const { toast } = useToast()
  const [includeLabels, setIncludeLabels] = useState(false)
  const [copying, setCopying] = useState(false)
  const [downloading, setDownloading] = useState(false)

  const venueEntries = useMemo(() => {
    return venues
      .map((venue) => {
        const url = buildVenueUrl(venue)
        if (!url) return null
        const label = describeVenue(venue)
        return { url, label }
      })
      .filter(Boolean)
  }, [venues])

  const handleCopyVenues = async () => {
    if (!venueEntries.length) {
      toast({
        title: 'No OpenAlex venue URLs',
        description: 'None of the venues expose an OpenAlex identifier to copy.',
        variant: 'destructive',
      })
      return
    }
    setCopying(true)
    try {
      const lines = venueEntries.map(({ url, label }) =>
        includeLabels && label ? `${label}: ${url}` : url
      )
      await navigator.clipboard.writeText(lines.join('\n'))
      toast({
        title: `Copied ${venueEntries.length} venue profile${
          venueEntries.length === 1 ? '' : 's'
        }`,
        description: includeLabels
          ? 'Names, stats, and URLs are ready to paste.'
          : 'One OpenAlex venue URL per line is ready to paste.',
        variant: 'success',
      })
    } catch (err) {
      console.error(err)
      toast({
        title: 'Unable to copy venue URLs',
        description: err?.message || 'Clipboard permission was denied.',
        variant: 'destructive',
      })
    } finally {
      setCopying(false)
    }
  }

  const handleDownloadVenues = async () => {
    if (!venueEntries.length) {
      toast({
        title: 'No OpenAlex venue URLs',
        description: 'None of the venues expose an OpenAlex identifier to download.',
        variant: 'destructive',
      })
      return
    }
    setDownloading(true)
    try {
      const lines = venueEntries.map(({ url, label }) =>
        includeLabels && label ? `${label}: ${url}` : url
      )
      downloadTextFile('venue_links.txt', lines.join('\n'))
      toast({
        title: `Downloaded ${venueEntries.length} venue link${
          venueEntries.length === 1 ? '' : 's'
        }`,
        description: 'Check your downloads folder for venue_links.txt.',
      })
    } catch (err) {
      console.error(err)
      toast({
        title: 'Unable to download venue URLs',
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
          <h2 className="text-2xl font-semibold text-gray-900">Top venues</h2>
          {venues.length ? (
            <div className="flex flex-wrap items-center gap-3 text-xs text-gray-600">
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  checked={includeLabels}
                  onChange={(event) => setIncludeLabels(event.target.checked)}
                />
                Include venue labels
              </label>
              <div className="flex flex-wrap items-center gap-2">
                <div className="flex flex-wrap gap-2">
                  <Button
                    variant="outline"
                    className="rounded-full"
                    onClick={handleCopyVenues}
                    disabled={copying}
                  >
                    {copying ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Copying…
                      </>
                    ) : (
                      'Copy venue URLs'
                    )}
                  </Button>
                  <Button
                    variant="outline"
                    className="rounded-full"
                    onClick={handleDownloadVenues}
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
                <CopyUsageHelp contextLabel="venue profile URLs" tooltip="Copy URL usage" />
              </div>
            </div>
          ) : null}
        </div>
        {venues.length ? (
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead className="text-left text-gray-500 border-b">
                <tr>
                  <th className="py-2 pr-4">Venue</th>
                  <th className="py-2 pr-4">Papers</th>
                  <th className="py-2 pr-4">Self</th>
                  <th className="py-2 pr-4">Citing</th>
                  <th className="py-2 pr-4">Cited</th>
                </tr>
              </thead>
              <tbody>
                {venues.slice(0, 10).map((venue) => (
                  <tr
                    key={venue.venue}
                    className={`border-b last:border-0 ${
                      onOpenVenue ? 'cursor-pointer hover:bg-gray-50 transition-colors' : ''
                    }`}
                    onClick={() => onOpenVenue?.(venue)}
                  >
                    <td className="py-3 pr-4 font-semibold text-gray-900">{venue.venue || '—'}</td>
                    <td className="py-3 pr-4 text-gray-700">{venue.total_papers}</td>
                    <td className="py-3 pr-4 text-gray-700">{venue.self_citations}</td>
                    <td className="py-3 pr-4 text-gray-700">{venue.citing_others}</td>
                    <td className="py-3 pr-4 text-gray-700">{venue.being_cited_by_others}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-sm text-gray-500">No venues available yet.</p>
        )}
      </div>
    </section>
  )
}
