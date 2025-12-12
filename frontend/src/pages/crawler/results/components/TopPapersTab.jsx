import { Button } from '@/components/ui/button'

import TopPaperCard from './TopPaperCard'

export default function TopPapersTab({
  papers,
  currentPage,
  pageSize,
  onPageChange,
  totalPages,
  onSelectPaper,
}) {
  return (
    <section className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-semibold text-gray-900">Influential papers</h2>
        <p className="text-sm text-gray-500">
          Showing{' '}
          {papers.length
            ? `${(currentPage - 1) * pageSize + 1}-${Math.min(currentPage * pageSize, papers.length)}`
            : 0}{' '}
          of {papers.length}.
        </p>
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
