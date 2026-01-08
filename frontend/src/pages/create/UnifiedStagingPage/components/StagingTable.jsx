import { AlertCircle, AlertTriangle, Check, Loader2, RefreshCw, X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { endpoints } from '@/shared/api/endpoints'
import config from '@/shared/config/env'
import SortableHead from './SortableHead'
import { FILTERABLE_COLUMNS } from '../constants'

export default function StagingTable({
  sessionId,
  stats,
  rows,
  loading,
  fetchError,
  totalFilteredRows,
  rangeStart,
  rangeEnd,
  sort,
  onToggleSort,
  onRefresh,
  onSelectVisible,
  onToggleSelectedSort,
  activeColumnFilterCount,
  columnFilters,
  columnCustomFilters,
  clearColumnFilter,
  clearAllColumnFilters,
  columnOptions,
  onApplyColumnFilter,
  onApplyCustomColumnFilter,
  onSelectRow,
  editing,
  onStartEditing,
  onChangeEditingValue,
  onCommitEditing,
  onCancelEditing,
  page,
  totalPages,
  onPreviousPage,
  onNextPage,
  onOpenManual,
  onOpenZotero,
  onOpenPdf,
  onResetFilters,
  onCheckRetractions,
  checkingRetractions,
  retractionSummary,
}) {
  const handleOpenSourceFile = (stagingId) => {
    if (!sessionId) return
    const baseUrl = (config.apiUrl || '').replace(/\/+$/, '')
    const path = `${endpoints.seedsSession}/${sessionId}/staging/${stagingId}/file`
    const url = `${baseUrl}${path}`
    window.open(url, '_blank', 'noopener,noreferrer')
  }

  const renderEditableValue = (row, field, placeholder, isTextArea = false) => {
    const isEditing = editing.id === row.staging_id && editing.field === field
    const displayValue = row[field]
    if (isEditing) {
      const inputClass =
        field === 'year'
          ? 'w-24 text-center rounded-full border border-gray-300 px-3 py-2 text-sm shadow-md focus:outline-none focus:ring-2 focus:ring-gray-900'
          : 'w-64 max-w-full rounded-full border border-gray-300 px-3 py-2 text-sm shadow-md focus:outline-none focus:ring-2 focus:ring-gray-900'
      const commonProps = {
        autoFocus: true,
        value: editing.value,
        onChange: (e) => onChangeEditingValue(e.target.value),
        onBlur: onCommitEditing,
        onKeyDown: (e) => {
          if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault()
            onCommitEditing()
          } else if (e.key === 'Escape') {
            onCancelEditing()
          }
        },
      }
      if (isTextArea) {
        return (
          <textarea
            rows={4}
            className="w-full min-w-[320px] rounded-3xl border border-gray-200 px-4 py-3 text-sm shadow-md focus:outline-none focus:ring-2 focus:ring-gray-900"
            {...commonProps}
          />
        )
      }
      return <input type={field === 'year' ? 'number' : 'text'} className={inputClass} {...commonProps} />
    }
    return (
      <div onDoubleClick={() => onStartEditing(row.staging_id, field, displayValue ?? '')} className="cursor-text">
        {displayValue ? (
          <span className="text-sm text-gray-900">{displayValue}</span>
        ) : (
          <span className="text-sm text-gray-400">{placeholder}</span>
        )}
      </div>
    )
  }

  const formatTimestamp = (value) => {
    if (!value) return null
    try {
      const date = new Date(value)
      if (Number.isNaN(date.getTime())) return null
      return date.toLocaleString()
    } catch (err) {
      return null
    }
  }

  const formatRetractionDate = (value) => {
    if (!value) return null
    const date = new Date(value)
    if (!Number.isNaN(date.getTime())) {
      return date.toLocaleDateString()
    }
    return value
  }

  const getRetractionTooltip = (row) => {
    const parts = []
    if (row.retraction_reason) {
      parts.push(`Reason: ${row.retraction_reason}`)
    }
    if (row.retraction_date) {
      parts.push(`Date: ${formatRetractionDate(row.retraction_date)}`)
    }
    if (!parts.length) {
      parts.push('Flagged by Retraction Watch')
    }
    return parts.join('\n')
  }

  return (
    <section className="flex-1 flex flex-col border border-gray-200 rounded-3xl bg-white shadow-md overflow-hidden">
      <div className="flex items-center justify-between px-6 py-3 border-b border-gray-100">
        <div className="text-sm text-gray-500">
          {stats.totalRows
            ? `Showing ${rangeStart && rangeEnd ? `${rangeStart}–${rangeEnd}` : '0'} of ${totalFilteredRows} papers (${stats.totalRows} staged total)`
            : 'No staged papers yet'}
        </div>
        <div className="flex items-center gap-2 text-sm text-gray-600">
          <button
            type="button"
            className="inline-flex items-center gap-1 text-xs text-gray-500 hover:text-gray-900"
            onClick={onRefresh}
          >
            <RefreshCw className="w-3 h-3" /> Refresh
          </button>
          <button
            type="button"
            className="inline-flex items-center gap-1 text-xs text-gray-500 hover:text-gray-900"
            onClick={() => onSelectVisible(true)}
          >
            <Check className="w-3 h-3" /> Select visible
          </button>
          <button
            type="button"
            className="inline-flex items-center gap-1 text-xs text-gray-500 hover:text-gray-900"
            onClick={() => onSelectVisible(false)}
          >
            <span className="text-base leading-none">×</span> Clear visible
          </button>
          <button
            type="button"
            className={`inline-flex items-center gap-1 text-xs ${
              sort.field === 'selected' ? 'text-gray-900 font-semibold' : 'text-gray-500 hover:text-gray-900'
            }`}
            onClick={onToggleSelectedSort}
          >
            {sort.field === 'selected' ? 'Selected first ✓' : 'Selected first'}
          </button>
          {stats.totalRows > 0 && (
            <Button
              type="button"
              variant="ghost"
              className="rounded-full text-xs text-white hover:opacity-85"
              style={{ backgroundColor: 'oklch(37.3% 0.034 259.733)' }}
              disabled={checkingRetractions}
              onClick={onCheckRetractions}
            >
              {checkingRetractions ? <Loader2 className="w-3 h-3 mr-1 animate-spin" /> : null}
              Check retractions
            </Button>
          )}
        </div>
      </div>
      {retractionSummary && (
        <div className="px-6 py-2 text-xs text-gray-600 border-b border-gray-100 bg-gray-50 flex items-center justify-between">
          <span>
            Last checked {formatTimestamp(retractionSummary.checked_at) || 'recently'} •{' '}
            <span className="font-semibold text-gray-900">{retractionSummary.retracted_count}</span> flagged
          </span>
          {retractionSummary.skipped_without_doi ? (
            <span className="text-gray-500">
              {retractionSummary.skipped_without_doi} without DOI skipped
            </span>
          ) : null}
        </div>
      )}
      {activeColumnFilterCount > 0 && (
        <div className="border-b border-gray-100 px-6 py-3 bg-gray-50 flex flex-wrap items-center gap-2">
          {FILTERABLE_COLUMNS.map(({ key, label }) => {
            const count = columnFilters[key]?.length || 0
            const hasCustom = Boolean(columnCustomFilters[key])
            if (!count && !hasCustom) return null
            const summary = hasCustom ? (count ? `${count} + custom` : 'custom') : `${count} selected`
            return (
              <button
                key={`chip-${key}`}
                type="button"
                className="inline-flex items-center gap-2 rounded-full bg-white border border-gray-200 px-3 py-1 text-xs text-gray-700 shadow-sm hover:border-gray-400"
                onClick={() => clearColumnFilter(key)}
              >
                <span className="font-semibold text-gray-900">{label}:</span>
                <span>{summary}</span>
                <X className="w-3 h-3" />
              </button>
            )
          })}
          <button
            type="button"
            className="text-xs text-gray-600 underline decoration-dotted hover:text-gray-900"
            onClick={clearAllColumnFilters}
          >
            Clear column filters
          </button>
        </div>
      )}
      {fetchError && (
        <div className="px-6 py-3 bg-red-50 text-sm text-red-700 flex items-center gap-2">
          <AlertCircle className="w-4 h-4" />
          {fetchError}
        </div>
      )}
      <div className="flex-1 overflow-auto">
        {loading ? (
          <div className="flex items-center justify-center py-12 text-gray-500 text-sm">
            <Loader2 className="w-4 h-4 mr-2 animate-spin" />
            Loading staged papers...
          </div>
        ) : rows.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 text-center px-6">
            <p className="text-lg font-semibold text-gray-800 mb-2">
              {stats.totalRows > 0 ? 'No papers match your current filters' : 'No papers staged yet'}
            </p>
            <p className="text-sm text-gray-500 mb-4">
              {stats.totalRows > 0
                ? 'Try adjusting the filters to see more staged papers.'
                : 'Use “Add more papers” to bring in seeds from manual IDs or other sources.'}
            </p>
            {stats.totalRows === 0 ? (
              <div className="flex flex-col sm:flex-row gap-3 w-full max-w-md">
                <Button variant="outline" className="rounded-full flex-1" onClick={onOpenManual}>
                  Manual IDs
                </Button>
                <Button variant="outline" className="rounded-full flex-1" onClick={onOpenZotero}>
                  Zotero collections
                </Button>
                <Button variant="outline" className="rounded-full flex-1" onClick={onOpenPdf}>
                  Uploaded files
                </Button>
              </div>
            ) : (
              <Button variant="outline" className="rounded-full" onClick={onResetFilters}>
                Clear filters
              </Button>
            )}
          </div>
        ) : (
          <table className="min-w-full divide-y divide-gray-100">
            <thead className="bg-gray-50 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
              <tr>
                <th className="px-4 py-3">
                  <input
                    type="checkbox"
                    className="rounded border-gray-300 text-gray-900 focus:ring-gray-900"
                    checked={rows.every((row) => row.is_selected)}
                    onChange={(e) => onSelectVisible(e.target.checked)}
                  />
                </th>
                <SortableHead label="Source" field="source" sort={sort} onToggle={onToggleSort} />
                <SortableHead
                  label="Title"
                  field="title"
                  sort={sort}
                  onToggle={onToggleSort}
                  filterKey="title"
                  filterOptions={columnOptions.title}
                  selectedFilters={columnFilters.title}
                  customFilter={columnCustomFilters.title}
                  onApplyFilter={onApplyColumnFilter}
                  onApplyCustomFilter={onApplyCustomColumnFilter}
                />
                <SortableHead
                  label="Authors"
                  field="authors"
                  sort={sort}
                  onToggle={onToggleSort}
                  filterKey="authors"
                  filterOptions={columnOptions.authors}
                  selectedFilters={columnFilters.authors}
                  customFilter={columnCustomFilters.authors}
                  onApplyFilter={onApplyColumnFilter}
                  onApplyCustomFilter={onApplyCustomColumnFilter}
                />
                <SortableHead
                  label="Year"
                  field="year"
                  sort={sort}
                  onToggle={onToggleSort}
                  filterKey="year"
                  filterOptions={columnOptions.year}
                  selectedFilters={columnFilters.year}
                  customFilter={columnCustomFilters.year}
                  onApplyFilter={onApplyColumnFilter}
                  onApplyCustomFilter={onApplyCustomColumnFilter}
                />
                <SortableHead
                  label="Venue"
                  field="venue"
                  sort={sort}
                  onToggle={onToggleSort}
                  filterKey="venue"
                  filterOptions={columnOptions.venue}
                  selectedFilters={columnFilters.venue}
                  customFilter={columnCustomFilters.venue}
                  onApplyFilter={onApplyColumnFilter}
                  onApplyCustomFilter={onApplyCustomColumnFilter}
                />
                <SortableHead
                  label="Identifiers"
                  sort={sort}
                  onToggle={null}
                  filterKey="identifier"
                  filterOptions={columnOptions.identifier}
                  selectedFilters={columnFilters.identifier}
                  customFilter={columnCustomFilters.identifier}
                  onApplyFilter={onApplyColumnFilter}
                  onApplyCustomFilter={onApplyCustomColumnFilter}
                />
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {rows.map((row) => {
                const retractionCheckedText = formatTimestamp(row.retraction_checked_at)
                return (
                  <tr
                    key={row.staging_id}
                    className={`transition-colors ${
                      row.is_selected ? 'bg-purple-50/70' : 'bg-white hover:bg-gray-50'
                    }`}
                  >
                  <td className="px-4 py-3 align-top">
                    <input
                      type="checkbox"
                      className="rounded border-gray-300 text-gray-900 focus:ring-gray-900"
                      checked={row.is_selected}
                      onChange={(e) => onSelectRow(row.staging_id, e.target.checked)}
                    />
                  </td>
                  <td className="px-4 py-3 align-top">
                    <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-gray-100 text-xs font-semibold text-gray-700 mb-1">
                      {row.source || '—'}
                    </div>
                    {row.source_type &&
                      !['manual', 'pdf', 'zotero'].includes(row.source_type) &&
                      row.source_type !== row.source && (
                        <div className="text-xs text-gray-500 uppercase tracking-wide">{row.source_type}</div>
                      )}
                    {row.source_file_name && (
                      <button
                        type="button"
                        className="mt-2 text-xs text-blue-600 underline decoration-dotted hover:text-blue-800"
                        onClick={() => handleOpenSourceFile(row.staging_id)}
                      >
                        Open {row.source_file_name}
                      </button>
                    )}
                    {row.is_retracted && (
                      <div className="mt-2 relative group inline-block">
                        <span className="inline-flex items-center gap-1 text-xs font-semibold text-red-700 bg-red-50 border border-red-200 rounded-full px-2 py-0.5">
                          <AlertTriangle className="w-3 h-3" />
                          Retracted
                        </span>
                        <div className="absolute z-10 hidden group-hover:block bg-gray-900 text-white text-xs rounded-xl px-3 py-2 mt-2 shadow-lg whitespace-pre-line max-w-xs">
                          {getRetractionTooltip(row)}
                        </div>
                      </div>
                    )}
                  </td>
                  <td className="px-4 py-3 align-top min-w-[220px]">
                    <div className="font-semibold text-gray-900 text-sm mb-1">
                      {renderEditableValue(row, 'title', 'Double-click to add title')}
                    </div>
                    {row.abstract ? (
                      <div className="text-xs text-gray-500 line-clamp-2">
                        {renderEditableValue(row, 'abstract', 'Double-click to add abstract', true)}
                      </div>
                    ) : (
                      <div className="text-xs text-gray-400">
                        {renderEditableValue(row, 'abstract', 'Double-click to add abstract', true)}
                      </div>
                    )}
                  </td>
                  <td className="px-4 py-3 align-top text-sm text-gray-700 min-w-[200px]">
                    {renderEditableValue(row, 'authors', 'Double-click to add authors')}
                  </td>
                  <td className="px-4 py-3 align-top text-sm text-gray-700 w-24 min-w-[96px]">
                    {renderEditableValue(row, 'year', 'Year')}
                  </td>
                  <td className="px-4 py-3 align-top text-sm text-gray-700 min-w-[180px]">
                    {renderEditableValue(row, 'venue', 'Double-click to add venue')}
                  </td>
                  <td className="px-4 py-3 align-top text-xs text-gray-600 space-y-2">
                    <div>
                      <div className="text-[10px] uppercase text-gray-400 mb-1">DOI</div>
                      {renderEditableValue(row, 'doi', 'Add DOI')}
                      {retractionCheckedText && (
                        <div className="text-[10px] text-gray-400 mt-1">Checked {retractionCheckedText}</div>
                      )}
                    </div>
                    <div>
                      <div className="text-[10px] uppercase text-gray-400 mb-1">URL</div>
                      {renderEditableValue(row, 'url', 'Add URL')}
                    </div>
                  </td>
                </tr>
                )
              })}
            </tbody>
          </table>
        )}
      </div>
      {rows.length > 0 && (
        <div className="border-t border-gray-100 px-6 py-4 flex items-center justify-between text-sm text-gray-600">
          <div>
            Page {page} of {totalPages}
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" className="rounded-full text-xs" disabled={page <= 1} onClick={onPreviousPage}>
              Previous
            </Button>
            <Button
              variant="outline"
              className="rounded-full text-xs"
              disabled={page >= totalPages}
              onClick={onNextPage}
            >
              Next
            </Button>
          </div>
        </div>
      )}
    </section>
  )
}
