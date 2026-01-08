export default function AuthorsTab({ authors, onOpenAuthor }) {
  return (
    <section className="space-y-6">
      <div className="rounded-3xl border border-gray-200 shadow-sm p-6">
        <h2 className="text-2xl font-semibold text-gray-900 mb-4">Top authors</h2>
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
