import { useEffect, useRef } from 'react'

import ColumnFilterButton from '@/components/column-filters/ColumnFilterButton'

import AnnotationMarkDropdown from './AnnotationMarkDropdown'
import { formatCentrality, getRowAnnotationClasses } from '../utils'

const CATALOG_SORT_COLUMN_MAP = {
  title: 'title',
  authors: 'authors_display',
  year: 'year',
  venue: 'venue',
  identifier: 'doi',
  citation_count: 'citation_count',
  centrality_in: 'centrality_in',
  centrality_out: 'centrality_out',
}

export default function CatalogTable({
  catalogPapers,
  columnFilters,
  columnCustomFilters,
  columnOptions,
  applyColumnFilter,
  applyColumnCustomFilter,
  fetchCatalogColumnOptions,
  catalogSort,
  onSortToggle,
  catalogEnabled,
  catalogLoading,
  annotationMarks,
  selectedPaperIds,
  onTogglePaperSelection,
  onToggleVisibleRows,
  allVisibleSelected,
  hasVisiblePapers,
  someVisibleSelected,
  markSavingIds,
  bulkMarkState,
  onInlineMarkChange,
  onOpenPaperDetails,
}) {
  const selectAllRef = useRef(null)

  useEffect(() => {
    if (selectAllRef.current) {
      selectAllRef.current.indeterminate = someVisibleSelected
    }
  }, [someVisibleSelected])

  const renderCatalogHeaderCell = (columnKey, label, widthClass, options = {}) => {
    const { enableFilter = true, sortKey = columnKey } = options
    const backendSortKey = CATALOG_SORT_COLUMN_MAP[sortKey]
    const isSortable = Boolean(backendSortKey)
    const isActiveSort = isSortable && catalogSort?.key === backendSortKey
    const sortIcon = isActiveSort ? (catalogSort.direction === 'asc' ? '↑' : '↓') : null

    return (
      <th className={`py-3 px-4 ${widthClass}`}>
        <div className="flex items-center gap-2">
          <button
            type="button"
            className={`inline-flex items-center gap-1 text-sm font-semibold text-gray-600 ${
              isSortable ? 'hover:text-gray-900' : 'cursor-default text-gray-400'
            }`}
            onClick={() => onSortToggle(sortKey)}
            disabled={!isSortable}
          >
            <span>{label}</span>
            {sortIcon ? <span>{sortIcon}</span> : null}
          </button>
          {enableFilter ? (
            <ColumnFilterButton
              columnKey={columnKey}
              label={label}
              options={columnOptions[columnKey] || []}
              selectedItems={columnFilters[columnKey]}
              customFilter={columnCustomFilters[columnKey]}
              onApply={(items) => applyColumnFilter(columnKey, items)}
              onApplyCustomFilter={(payload) => applyColumnCustomFilter(columnKey, payload)}
              fetchOptions={
                fetchCatalogColumnOptions
                  ? (params) => fetchCatalogColumnOptions(columnKey, params)
                  : null
              }
            />
          ) : null}
        </div>
      </th>
    )
  }

  return (
    <div className="overflow-x-auto rounded-3xl border border-gray-200 shadow-sm">
      <table className="min-w-[2000px] text-sm">
        <thead className="text-left text-gray-500 border-b bg-gray-50">
          <tr>
            <th className="py-3 px-4 w-12">
              <input
                ref={selectAllRef}
                type="checkbox"
                className="h-4 w-4 rounded border-gray-300 text-gray-900 focus:ring-gray-400"
                checked={hasVisiblePapers && allVisibleSelected}
                onChange={onToggleVisibleRows}
              />
            </th>
            {renderCatalogHeaderCell('title', 'Title', 'w-[420px]')}
            {renderCatalogHeaderCell('authors', 'Authors', 'w-[360px]')}
            {renderCatalogHeaderCell('year', 'Year', 'w-[90px]')}
            {renderCatalogHeaderCell('venue', 'Venue', 'w-[240px]')}
            {renderCatalogHeaderCell('identifier', 'DOI', 'w-[320px]')}
            {renderCatalogHeaderCell('citation_count', 'Citations', 'w-[110px]', {
              enableFilter: false,
              sortKey: 'citation_count',
            })}
            {renderCatalogHeaderCell('centrality_in', 'Centrality (in)', 'w-[160px]', {
              enableFilter: false,
              sortKey: 'centrality_in',
            })}
            {renderCatalogHeaderCell('centrality_out', 'Centrality (out)', 'w-[160px]', {
              enableFilter: false,
              sortKey: 'centrality_out',
            })}
            <th className="py-3 px-4 w-[300px]">Topics</th>
            <th className="py-3 px-4 w-[180px]">Status</th>
            <th className="py-3 px-4 w-[150px]">Mark</th>
          </tr>
        </thead>
        <tbody>
          {catalogPapers.map((paper) => {
            const rowSelected = selectedPaperIds.has(paper.paper_id)
            const markValue = paper.mark || 'standard'
            const rowMarkLoading = markSavingIds.has(paper.paper_id)
            return (
              <tr key={paper.paper_id} className={`${getRowAnnotationClasses(markValue)} border-b last:border-0`}>
                <td className="py-3 px-4 align-top w-12">
                  <input
                    type="checkbox"
                    className="h-4 w-4 rounded border-gray-300 text-gray-900 focus:ring-gray-400"
                    checked={rowSelected}
                    onChange={() => onTogglePaperSelection(paper.paper_id)}
                  />
                </td>
                <td className="py-3 px-4 align-top w-[420px]">
                  <button
                    type="button"
                    onClick={() => onOpenPaperDetails(paper)}
                    className="text-left w-full"
                  >
                    <p className="font-semibold text-gray-900 hover:underline">
                      {paper.title || paper.paper_id || 'Untitled paper'}
                    </p>
                    <p className="text-xs text-gray-500 font-mono">{paper.paper_id}</p>
                    <div className="flex flex-wrap gap-2 mt-2 text-[11px] uppercase tracking-wide">
                      {paper.is_seed ? (
                        <span className="px-2 py-0.5 rounded-full bg-gray-100 text-gray-700">
                          Seed
                        </span>
                      ) : null}
                      {paper.is_retracted ? (
                        <span className="px-2 py-0.5 rounded-full bg-red-100 text-red-700">
                          Retracted
                        </span>
                      ) : null}
                    </div>
                  </button>
                </td>
                <td className="py-3 px-4 text-gray-700 align-top w-[360px]">
                  {paper.authors?.length ? paper.authors.join(', ') : 'Unknown authors'}
                </td>
                <td className="py-3 px-4 text-gray-700 align-top w-[90px]">{paper.year || '—'}</td>
                <td className="py-3 px-4 text-gray-700 align-top w-[240px]">{paper.venue || '—'}</td>
                <td className="py-3 px-4 text-gray-700 align-top w-[320px]">
                  {paper.doi ? (
                    <a
                      href={`https://doi.org/${paper.doi}`}
                      target="_blank"
                      rel="noreferrer"
                      className="text-blue-600 hover:underline break-all"
                    >
                      {paper.doi}
                    </a>
                  ) : (
                    '—'
                  )}
                </td>
                <td className="py-3 px-4 text-gray-700 align-top w-[110px]">
                  {typeof paper.citation_count === 'number' ? paper.citation_count : '—'}
                </td>
                <td className="py-3 px-4 text-gray-700 align-top w-[160px]">
                  {formatCentrality(paper.centrality_in)}
                </td>
                <td className="py-3 px-4 text-gray-700 align-top w-[160px]">
                  {formatCentrality(paper.centrality_out)}
                </td>
                <td className="py-3 px-4 text-gray-700 align-top w-[300px]">
                  <div className="flex flex-wrap gap-2">
                    {typeof paper.nmf_topic === 'number' ? (
                      <span className="px-2 py-0.5 rounded-full bg-gray-100 text-xs text-gray-700">
                        NMF #{paper.nmf_topic}
                      </span>
                    ) : null}
                    {typeof paper.lda_topic === 'number' ? (
                      <span className="px-2 py-0.5 rounded-full bg-gray-100 text-xs text-gray-700">
                        LDA #{paper.lda_topic}
                      </span>
                    ) : null}
                  </div>
                </td>
                <td className="py-3 px-4 text-gray-700 align-top w-[180px]">
                  <div className="flex flex-wrap gap-2">
                    {renderBooleanBadge(paper.selected, 'Selected', 'blue')}
                    {renderBooleanBadge(paper.is_seed, 'Seed', 'green')}
                    {renderBooleanBadge(paper.is_retracted, 'Retracted', 'red')}
                  </div>
                </td>
                <td className="py-3 px-4 text-gray-700 align-top w-[150px]">
                  <AnnotationMarkDropdown
                    value={markValue}
                    disabled={rowMarkLoading || catalogLoading || !catalogEnabled || bulkMarkState.loading}
                    loading={rowMarkLoading}
                    onChange={(nextValue) => onInlineMarkChange(paper.paper_id, nextValue)}
                    marks={annotationMarks}
                  />
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}

function renderBooleanBadge(value, truthyLabel, color) {
  if (!value) return null
  const classes = {
    green: 'bg-green-100 text-green-700',
    gray: 'bg-gray-100 text-gray-700',
    red: 'bg-red-100 text-red-700',
    blue: 'bg-blue-100 text-blue-700',
  }
  return (
    <span className={`px-2 py-0.5 rounded-full text-[11px] uppercase ${classes[color] || classes.gray}`}>
      {truthyLabel}
    </span>
  )
}
