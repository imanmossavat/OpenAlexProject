export default function VenuesTab({ venues, onOpenVenue }) {
  return (
    <section className="space-y-6">
      <div className="rounded-3xl border border-gray-200 shadow-sm p-6">
        <h2 className="text-2xl font-semibold text-gray-900 mb-4">Top venues</h2>
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
