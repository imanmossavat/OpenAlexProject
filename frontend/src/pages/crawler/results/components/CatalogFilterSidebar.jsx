import { useState } from 'react'
import { ChevronDown, Filter } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

import FilterSection from './FilterSection'

const DOI_FILTER_OPTIONS = [
  { value: 'all', label: 'All' },
  { value: 'with', label: 'With DOI' },
  { value: 'without', label: 'No DOI' },
]

const SEED_FILTER_OPTIONS = [
  { value: 'all', label: 'All' },
  { value: 'with', label: 'Seeded' },
  { value: 'without', label: 'Not seeded' },
]

const RETRACTION_FILTER_OPTIONS = [
  { value: 'all', label: 'All' },
  { value: 'with', label: 'Retracted' },
  { value: 'without', label: 'Not retracted' },
]

export default function CatalogFilterSidebar({
  catalogEnabled,
  activeGeneralFilterCount,
  catalogSearchDraft,
  onCatalogSearchChange,
  onCatalogSearchSubmit,
  onCatalogSearchReset,
  catalogVenueDraft,
  onCatalogVenueChange,
  onCatalogVenueSubmit,
  onCatalogVenueReset,
  catalogYearFromDraft,
  catalogYearToDraft,
  onCatalogYearFromChange,
  onCatalogYearToChange,
  onCatalogYearSubmit,
  onCatalogYearReset,
  availableTopicFilters,
  selectedTopicIds,
  onTopicToggle,
  onTopicSelectAll,
  onTopicFiltersReset,
  annotationMarks,
  annotationSelection,
  onAnnotationToggle,
  onAnnotationSelectAll,
  catalogFilters,
  onPresenceFilterChange,
  onSidebarReset,
}) {
  const [filtersOpen, setFiltersOpen] = useState(true)

  return (
    <aside className="w-full lg:w-72">
      <div className="rounded-3xl border border-gray-200 bg-white shadow-sm p-4 space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-gray-500" />
            <span className="text-sm font-semibold text-gray-700">Filters</span>
            {activeGeneralFilterCount > 0 ? (
              <span className="text-xs bg-gray-900 text-white rounded-full px-2 py-0.5">
                {activeGeneralFilterCount}
              </span>
            ) : null}
          </div>
          <button
            type="button"
            onClick={() => setFiltersOpen((prev) => !prev)}
            className="text-xs text-gray-500 hover:text-gray-900 inline-flex items-center gap-1"
          >
            {filtersOpen ? 'Hide' : 'Show'}
            <ChevronDown
              className={`w-3 h-3 transition-transform duration-200 ${
                filtersOpen ? 'rotate-180' : ''
              }`}
            />
          </button>
        </div>
        {filtersOpen ? (
          <div className="space-y-2">
            <FilterSection title="Search catalog" defaultOpen>
              <form onSubmit={onCatalogSearchSubmit} className="space-y-2">
                <Input
                  id="catalog-search"
                  type="text"
                  placeholder="Search by title or paper ID"
                  value={catalogSearchDraft}
                  onChange={(event) => onCatalogSearchChange(event.target.value)}
                  className="rounded-full shadow-sm border-gray-200 placeholder:text-gray-400"
                  disabled={!catalogEnabled}
                />
                <div className="flex gap-2">
                  <Button type="submit" className="rounded-full" disabled={!catalogEnabled}>
                    Apply
                  </Button>
                  <Button
                    type="button"
                    variant="outline"
                    className="rounded-full"
                    onClick={onCatalogSearchReset}
                    disabled={!catalogFilters.search}
                  >
                    Clear
                  </Button>
                </div>
                <p className="text-xs text-gray-500">Matches paper titles and identifiers.</p>
              </form>
            </FilterSection>
            <FilterSection title="Venue" defaultOpen>
              <form onSubmit={onCatalogVenueSubmit} className="space-y-2">
                <Label htmlFor="catalog-venue" className="text-xs uppercase tracking-[0.3em] text-gray-500">
                  Venue
                </Label>
                <Input
                  id="catalog-venue"
                  type="text"
                  placeholder="Venue name"
                  value={catalogVenueDraft}
                  onChange={(event) => onCatalogVenueChange(event.target.value)}
                  disabled={!catalogEnabled}
                  className="rounded-full shadow-sm border-gray-200 placeholder:text-gray-400"
                />
                <div className="flex gap-2">
                  <Button type="submit" className="rounded-full" disabled={!catalogEnabled}>
                    Apply
                  </Button>
                  <Button
                    type="button"
                    variant="outline"
                    className="rounded-full"
                    onClick={onCatalogVenueReset}
                    disabled={!catalogEnabled && !catalogVenueDraft}
                  >
                    Clear
                  </Button>
                </div>
              </form>
            </FilterSection>
            <FilterSection title="Year range" defaultOpen>
              <form onSubmit={onCatalogYearSubmit} className="space-y-2">
                <div className="flex gap-2">
                  <Input
                    type="number"
                    placeholder="From"
                    value={catalogYearFromDraft}
                    onChange={(event) => onCatalogYearFromChange(event.target.value)}
                    disabled={!catalogEnabled}
                    className="rounded-full shadow-sm border-gray-200 placeholder:text-gray-400"
                  />
                  <Input
                    type="number"
                    placeholder="To"
                    value={catalogYearToDraft}
                    onChange={(event) => onCatalogYearToChange(event.target.value)}
                    disabled={!catalogEnabled}
                    className="rounded-full shadow-sm border-gray-200 placeholder:text-gray-400"
                  />
                </div>
                <div className="flex gap-2">
                  <Button type="submit" className="rounded-full" disabled={!catalogEnabled}>
                    Apply
                  </Button>
                  <Button
                    type="button"
                    variant="outline"
                    className="rounded-full"
                    onClick={onCatalogYearReset}
                    disabled={!catalogEnabled && !catalogYearFromDraft && !catalogYearToDraft}
                  >
                    Clear
                  </Button>
                </div>
              </form>
            </FilterSection>
            <FilterSection title="Topics" defaultOpen>
              {availableTopicFilters.length ? (
                <div className="space-y-2">
                  <div className="space-y-2">
                    {availableTopicFilters.map((topic) => (
                      <label
                        key={topic.id}
                        className="flex items-center justify-between gap-2 text-sm text-gray-700"
                      >
                        <div className="flex items-center gap-2">
                          <input
                            type="checkbox"
                            className="rounded border-gray-300 text-gray-900 focus:ring-gray-900"
                            checked={selectedTopicIds.includes(topic.id)}
                            onChange={() => onTopicToggle(topic.id)}
                            disabled={!catalogEnabled}
                          />
                          <span>{topic.label}</span>
                        </div>
                        {typeof topic.paperCount === 'number' ? (
                          <span className="text-xs text-gray-500">{topic.paperCount} papers</span>
                        ) : null}
                      </label>
                    ))}
                  </div>
                  <div className="pt-2 flex flex-wrap gap-4 text-xs text-gray-500">
                    <button
                      type="button"
                      className="underline disabled:text-gray-300"
                      onClick={onTopicSelectAll}
                      disabled={!catalogEnabled}
                    >
                      Select all
                    </button>
                    <button
                      type="button"
                      className="underline disabled:text-gray-300"
                      onClick={onTopicFiltersReset}
                      disabled={!catalogEnabled || selectedTopicIds.length === 0}
                    >
                      Clear
                    </button>
                  </div>
                </div>
              ) : (
                <p className="text-xs text-gray-500">No topics available.</p>
              )}
            </FilterSection>
            <FilterSection title="Annotation marks" defaultOpen>
              <div className="space-y-2">
                {annotationMarks.map((mark) => (
                  <label key={mark.value} className="flex items-center gap-2 text-sm text-gray-700">
                    <input
                      type="checkbox"
                      className="rounded border-gray-300 text-gray-900 focus:ring-gray-900"
                      checked={annotationSelection.has(mark.value)}
                      onChange={() => onAnnotationToggle(mark.value)}
                      disabled={!catalogEnabled}
                    />
                    <span className="flex items-center gap-2">
                      <span className={`h-2.5 w-2.5 rounded-full ${mark.swatchClass}`} />
                      <span>{mark.label}</span>
                    </span>
                  </label>
                ))}
              </div>
              <div className="pt-2">
                <button
                  type="button"
                  className="text-xs text-gray-500 underline disabled:text-gray-300"
                  onClick={onAnnotationSelectAll}
                  disabled={!catalogEnabled}
                >
                  Select all
                </button>
              </div>
            </FilterSection>
            <FilterSection title="DOI" defaultOpen>
              <div className="flex flex-wrap gap-2">
                {DOI_FILTER_OPTIONS.map((option) => (
                  <Button
                    key={option.value}
                    type="button"
                    variant={catalogFilters.doiFilter === option.value ? 'default' : 'outline'}
                    className="rounded-full text-xs shadow-sm"
                    onClick={() => onPresenceFilterChange('doiFilter', option.value)}
                    disabled={!catalogEnabled}
                  >
                    {option.label}
                  </Button>
                ))}
              </div>
            </FilterSection>
            <FilterSection title="Seed papers" defaultOpen>
              <div className="flex flex-wrap gap-2">
                {SEED_FILTER_OPTIONS.map((option) => (
                  <Button
                    key={option.value}
                    type="button"
                    variant={catalogFilters.seedFilter === option.value ? 'default' : 'outline'}
                    className="rounded-full text-xs shadow-sm"
                    onClick={() => onPresenceFilterChange('seedFilter', option.value)}
                    disabled={!catalogEnabled}
                  >
                    {option.label}
                  </Button>
                ))}
              </div>
            </FilterSection>
            <FilterSection title="Retracted papers" defaultOpen>
              <div className="flex flex-wrap gap-2">
                {RETRACTION_FILTER_OPTIONS.map((option) => (
                  <Button
                    key={option.value}
                    type="button"
                    variant={catalogFilters.retractionFilter === option.value ? 'default' : 'outline'}
                    className="rounded-full text-xs shadow-sm"
                    onClick={() => onPresenceFilterChange('retractionFilter', option.value)}
                    disabled={!catalogEnabled}
                  >
                    {option.label}
                  </Button>
                ))}
              </div>
            </FilterSection>
            <Button
              type="button"
              variant="ghost"
              className="w-full rounded-full bg-gray-100 shadow-sm text-sm"
              onClick={onSidebarReset}
              disabled={!catalogEnabled && activeGeneralFilterCount === 0}
            >
              Clear filters
            </Button>
          </div>
        ) : (
          <div className="text-xs text-gray-500 space-y-2">
            <p>Filters are hidden. Use the button above to adjust them.</p>
            <Button variant="outline" className="w-full rounded-full text-xs" onClick={() => setFiltersOpen(true)}>
              Show filters
            </Button>
          </div>
        )}
      </div>
    </aside>
  )
}
