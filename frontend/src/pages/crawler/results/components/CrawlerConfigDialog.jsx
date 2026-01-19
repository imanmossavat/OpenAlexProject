import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'

const formatValue = (value) => {
  if (value === null || value === undefined || value === '') return '—'
  if (typeof value === 'boolean') return value ? 'Enabled' : 'Disabled'
  if (Array.isArray(value)) {
    if (!value.length) return '—'
    return value.join(', ')
  }
  if (typeof value === 'object') {
    const entries = Object.entries(value || {})
    if (!entries.length) return '—'
    return entries.map(([key, val]) => `${key}: ${val}`).join(' • ')
  }
  return String(value)
}

const ChipList = ({ label, items }) => (
  <div className="space-y-1">
    <p className="text-xs uppercase tracking-[0.2em] text-gray-400">{label}</p>
    {items?.length ? (
      <div className="flex flex-wrap gap-2">
        {items.map((item, index) => (
          <span
            key={`${item}-${index}`}
            className="px-2 py-1 rounded-full bg-gray-100 text-xs text-gray-700 break-words"
          >
            {item}
          </span>
        ))}
      </div>
    ) : (
      <p className="text-sm text-gray-500">—</p>
    )}
  </div>
)

const KeyValueRow = ({ label, value }) => (
  <div>
    <dt className="text-xs uppercase tracking-[0.2em] text-gray-400">{label}</dt>
    <dd className="text-gray-900 break-words">{formatValue(value)}</dd>
  </div>
)

export default function CrawlerConfigDialog({ open, onOpenChange, config, iterations }) {
  if (!config) return null
  const {
    job_name: jobName,
    display_name: displayName,
    library,
    keywords,
    seeds,
    crawler,
    api,
    sampling,
    text_processing: textProcessing,
    graph,
    retraction,
    output,
  } = config

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-3xl bg-white rounded-3xl border-0 shadow-2xl">
        <DialogHeader>
          <DialogTitle>Crawl configuration</DialogTitle>
          <p className="text-sm text-gray-500">Snapshot of the settings used for this crawler job.</p>
        </DialogHeader>
        <div className="space-y-6 text-sm text-gray-700 max-h-[70vh] overflow-y-auto pr-2">
          <section className="space-y-3">
            <div className="rounded-2xl border border-gray-200 p-4 space-y-4">
              <dl className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <KeyValueRow label="Job name" value={displayName || jobName} />
                <KeyValueRow
                  label="Library reference"
                  value={
                    library?.name || library?.path
                      ? [library?.name, library?.path].filter(Boolean).join(' — ')
                      : null
                  }
                />
                <KeyValueRow label="Max iterations" value={crawler?.max_iterations} />
                <KeyValueRow label="Iterations completed" value={iterations} />
                <KeyValueRow label="Papers per iteration" value={crawler?.papers_per_iteration} />
                <KeyValueRow label="API provider" value={api?.provider} />
              </dl>
              <div className="grid gap-4">
                <ChipList label="Keywords" items={keywords} />
                <ChipList label="Seed papers" items={seeds} />
              </div>
            </div>
          </section>

          <section className="space-y-2">
            <h3 className="text-base font-semibold text-gray-900">Topic modeling & language</h3>
            <div className="rounded-2xl border border-gray-200 p-4">
              <dl className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <KeyValueRow label="Topic model" value={textProcessing?.topic_model} />
                <KeyValueRow label="Number of topics" value={textProcessing?.num_topics} />
                <KeyValueRow label="Language" value={textProcessing?.language} />
                <KeyValueRow label="Save figures" value={textProcessing?.save_figures} />
              </dl>
            </div>
          </section>

          <section className="space-y-2">
            <h3 className="text-base font-semibold text-gray-900">Sampling & graph</h3>
            <div className="rounded-2xl border border-gray-200 p-4 space-y-4">
              <ChipList label="Ignored venues" items={sampling?.ignored_venues} />
              <dl className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <KeyValueRow
                  label="Include author nodes"
                  value={graph?.include_author_nodes}
                />
              </dl>
            </div>
          </section>

          <section className="space-y-2">
            <h3 className="text-base font-semibold text-gray-900">Retraction & output</h3>
            <div className="rounded-2xl border border-gray-200 p-4 space-y-4">
              <dl className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <KeyValueRow
                  label="Enable retraction watch"
                  value={retraction?.enable_retraction_watch}
                />
                <KeyValueRow label="Root folder" value={output?.root_folder} />
              </dl>
            </div>
          </section>
        </div>
      </DialogContent>
    </Dialog>
  )
}
