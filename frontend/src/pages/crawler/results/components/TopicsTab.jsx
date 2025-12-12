export default function TopicsTab({ topics, onOpenTopic, jobId }) {
  return (
    <section className="space-y-4">
      <h2 className="text-2xl font-semibold text-gray-900">Topics</h2>
      {topics.length ? (
        <div className="grid gap-4 md:grid-cols-2">
          {topics.map((topic) => (
            <div
              key={topic.topic_id}
              className="rounded-3xl border border-gray-200 shadow-sm p-6 space-y-3"
            >
              <div className="flex items-center justify-between">
                <p className="text-lg font-semibold text-gray-900">Topic {topic.topic_id}</p>
                <span className="text-xs text-gray-500">{topic.paper_count} papers</span>
              </div>
              <div className="flex flex-wrap gap-2">
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
      ) : (
        <p className="text-sm text-gray-500">No topics available yet.</p>
      )}
    </section>
  )
}
