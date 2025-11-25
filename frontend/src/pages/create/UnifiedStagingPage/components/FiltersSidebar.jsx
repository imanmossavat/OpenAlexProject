import { Filter, ChevronDown, ChevronRight } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

export default function FiltersSidebar({
  filters,
  availableSources,
  collapsed = false,
  activeFilterCount = 0,
  onToggleCollapse,
  onToggleSource,
  onFilterChange,
  onReset,
}) {
  const Chevron = collapsed ? ChevronRight : ChevronDown
  return (
    <aside
      className={`w-full ${collapsed ? 'max-w-[220px]' : 'max-w-xs'} border border-gray-200 rounded-3xl p-4 mr-6 bg-white shadow-md h-fit`}
    >
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-gray-500" />
          <span className="text-sm font-semibold text-gray-700">Filters</span>
          {activeFilterCount > 0 && (
            <span className="text-xs bg-gray-900 text-white rounded-full px-2 py-0.5">{activeFilterCount}</span>
          )}
        </div>
        <button
          type="button"
          onClick={onToggleCollapse}
          className="text-xs text-gray-500 hover:text-gray-900 inline-flex items-center gap-1"
        >
          {collapsed ? 'Show' : 'Hide'}
          <Chevron className="w-3 h-3" />
        </button>
      </div>
      {collapsed ? (
        <div className="text-xs text-gray-500 space-y-2">
          <p>Filters are hidden. Use the button above to adjust them.</p>
          <Button variant="outline" className="w-full rounded-full text-xs" onClick={onToggleCollapse}>
            Show filters
          </Button>
        </div>
      ) : (
        <div className="space-y-4">
        <div>
          <Label className="text-xs uppercase tracking-wider text-gray-500 mb-2 block">Source</Label>
          <div className="space-y-2 rounded-2xl border border-gray-100 p-3 shadow-md">
            {availableSources.length === 0 && (
              <p className="text-xs text-gray-400">Sources appear once you add papers.</p>
            )}
            {availableSources.map((source) => (
              <label key={source} className="flex items-center gap-2 text-sm text-gray-700">
                <input
                  type="checkbox"
                  className="rounded border-gray-300 text-gray-900 focus:ring-gray-900"
                  checked={filters.sources.includes(source)}
                  onChange={() => onToggleSource(source)}
                />
                {source}
              </label>
            ))}
          </div>
        </div>

        <div>
          <Label className="text-xs uppercase tracking-wider text-gray-500 mb-1 block">Year range</Label>
          <div className="flex items-center gap-2">
            <Input
              type="number"
              placeholder="From"
              value={filters.yearMin}
              className="rounded-full shadow-sm"
              onChange={(e) => onFilterChange('yearMin', e.target.value)}
            />
            <span className="text-sm text-gray-400">—</span>
            <Input
              type="number"
              placeholder="To"
              value={filters.yearMax}
              className="rounded-full shadow-sm"
              onChange={(e) => onFilterChange('yearMax', e.target.value)}
            />
          </div>
        </div>

        <div>
          <Label className="text-xs uppercase tracking-wider text-gray-500 mb-1 block">Title search</Label>
          <Input
            placeholder="e.g. Transformer"
            value={filters.title}
            className="rounded-full shadow-sm"
            onChange={(e) => onFilterChange('title', e.target.value)}
          />
        </div>

        <div>
          <Label className="text-xs uppercase tracking-wider text-gray-500 mb-1 block">Author search</Label>
          <Input
            placeholder="Author name"
            value={filters.author}
            className="rounded-full shadow-sm"
            onChange={(e) => onFilterChange('author', e.target.value)}
          />
        </div>

        <div>
          <Label className="text-xs uppercase tracking-wider text-gray-500 mb-1 block">Venue search</Label>
          <Input
            placeholder="Journal, conference..."
            value={filters.venue}
            className="rounded-full shadow-sm"
            onChange={(e) => onFilterChange('venue', e.target.value)}
          />
        </div>

        <div>
          <Label className="text-xs uppercase tracking-wider text-gray-500 mb-1 block">Keyword / tag</Label>
          <Input
            placeholder="Search title or abstract"
            value={filters.keyword}
            className="rounded-full shadow-sm"
            onChange={(e) => onFilterChange('keyword', e.target.value)}
          />
        </div>

        <div>
          <Label className="text-xs uppercase tracking-wider text-gray-500 mb-1 block">DOI filter</Label>
          <div className="flex items-center gap-2">
            {[
              { label: 'All', value: 'all' },
              { label: 'With DOI', value: 'with' },
              { label: 'No DOI', value: 'without' },
            ].map((opt) => (
              <button
                type="button"
                key={opt.value}
                className={`px-4 py-1.5 rounded-full text-xs font-medium border shadow-md ${
                  filters.doi === opt.value
                    ? 'bg-gray-900 text-white border-gray-900'
                    : 'bg-white text-gray-600 border-gray-200 hover:border-gray-400'
                }`}
                onClick={() => onFilterChange('doi', opt.value)}
              >
                {opt.label}
              </button>
            ))}
          </div>
        </div>

        <div>
          <Label className="text-xs uppercase tracking-wider text-gray-500 mb-1 block">Retractions</Label>
          <div className="flex items-center gap-2">
            {[
              { label: 'All', value: 'all' },
              { label: 'Retracted', value: 'retracted' },
              { label: 'Clean', value: 'clean' },
            ].map((opt) => (
              <button
                type="button"
                key={opt.value}
                className={`px-4 py-1.5 rounded-full text-xs font-medium border shadow-md ${
                  filters.retraction === opt.value
                    ? 'bg-gray-900 text-white border-gray-900'
                    : 'bg-white text-gray-600 border-gray-200 hover:border-gray-400'
                }`}
                onClick={() => onFilterChange('retraction', opt.value)}
              >
                {opt.label}
              </button>
            ))}
          </div>
        </div>

        <label className="flex items-center gap-2 text-sm text-gray-700">
          <input
            type="checkbox"
            className="rounded border-gray-300 text-gray-900 focus:ring-gray-900"
            checked={filters.selectedOnly}
            onChange={(e) => onFilterChange('selectedOnly', e.target.checked)}
          />
          Show selected only
        </label>

        <Button variant="ghost" className="w-full rounded-full bg-gray-100 shadow-sm" onClick={onReset}>
          Clear filters
        </Button>
        </div>
      )}
    </aside>
  )
}
