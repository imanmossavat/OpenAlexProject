import { Button } from '@/components/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { useToast } from '@/hooks/use-toast'

import TopPaperCard from './TopPaperCard'
import { downloadTextFile, getPreferredPaperUrl } from '../utils'

export default function TopPapersTab({
  papers,
  currentPage,
  pageSize,
  onPageChange,
  totalPages,
  onSelectPaper,
  centralityMetric,
  onCentralityMetricChange,
}) {
  const { toast } = useToast()
  const metricOptions = [
    { value: 'centrality_in', label: 'Centrality (In)' },
    { value: 'centrality_out', label: 'Centrality (Out)' },
  ]
  return (
    <section className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-semibold text-gray-900">Influential papers</h2>
        <div className="flex items-center gap-4">
          <div className="text-sm text-gray-500">
            Showing{' '}
            {papers.length
              ? `${(currentPage - 1) * pageSize + 1}-${Math.min(currentPage * pageSize, papers.length)}`
              : 0}{' '}
            of {papers.length}.
          </div>
          <div className="flex items-center gap-2 text-xs text-gray-600">
            <span className="uppercase tracking-[0.3em] text-gray-400">Sort by</span>
            <Select value={centralityMetric} onValueChange={onCentralityMetricChange}>
              <SelectTrigger className="h-9 rounded-full border border-gray-200 px-3 pr-8 text-xs shadow-sm w-[180px] bg-white">
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="rounded-2xl border border-gray-200 bg-white shadow-lg">
                {metricOptions.map((option) => (
                  <SelectItem key={option.value} value={option.value}>
                    {option.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              className="rounded-full"
              onClick={async () => {
                const urls = papers
                  .map((paper) => getPreferredPaperUrl(paper))
                  .filter((value) => value && value.length > 0)
                if (!urls.length) {
                  toast({
                    title: 'No links available',
                    description: 'None of the visible papers have source URLs.',
                    variant: 'destructive',
                  })
                  return
                }
                try {
                  await navigator.clipboard.writeText(urls.join('\n'))
                  toast({
                    title: `Copied ${urls.length} top paper link${urls.length === 1 ? '' : 's'}`,
                    description: 'Ready to paste into NotebookLM or other tools.',
                    variant: 'success',
                  })
                } catch (err) {
                  toast({
                    title: 'Unable to copy links',
                    description: 'Clipboard permission was denied.',
                    variant: 'destructive',
                  })
                }
              }}
            >
              Copy URLs
            </Button>
            <Button
              variant="outline"
              className="rounded-full"
              onClick={() => {
                const urls = papers
                  .map((paper) => getPreferredPaperUrl(paper))
                  .filter((value) => value && value.length > 0)
                if (!urls.length) {
                  toast({
                    title: 'No links available',
                    description: 'None of the visible papers have source URLs.',
                    variant: 'destructive',
                  })
                  return
                }
                downloadTextFile('top_papers_links.txt', urls.join('\n'))
                toast({
                  title: `Downloaded ${urls.length} link${urls.length === 1 ? '' : 's'}`,
                  description: 'Check your downloads for top_papers_links.txt.',
                })
              }}
            >
              Download TXT
            </Button>
          </div>
        </div>
      </div>
      {papers.length ? (
        <>
          <div className="space-y-4">
            {papers
              .slice((currentPage - 1) * pageSize, currentPage * pageSize)
              .map((paper, idx) => (
                <TopPaperCard
                  key={paper.paper_id}
                  paper={paper}
                  rank={(currentPage - 1) * pageSize + idx + 1}
                  onSelect={onSelectPaper}
                  centralityMetric={centralityMetric}
                />
              ))}
          </div>
          {totalPages > 1 && (
            <div className="flex items-center justify-between pt-4">
              <p className="text-sm text-gray-500">
                Page {currentPage} of {totalPages}
              </p>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  className="rounded-full"
                  onClick={() => onPageChange(currentPage - 1)}
                  disabled={currentPage === 1}
                >
                  Previous
                </Button>
                <Button
                  variant="outline"
                  className="rounded-full"
                  onClick={() => onPageChange(currentPage + 1)}
                  disabled={currentPage === totalPages}
                >
                  Next
                </Button>
              </div>
            </div>
          )}
        </>
      ) : (
        <p className="text-sm text-gray-500">No papers available yet.</p>
      )}
    </section>
  )
}
