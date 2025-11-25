import ColumnFilterButton from './ColumnFilterButton'

export default function SortableHead({
  label,
  field,
  sort,
  onToggle,
  filterKey,
  filterOptions,
  selectedFilters,
  customFilter,
  onApplyFilter,
  onApplyCustomFilter,
}) {
  const isSortable = Boolean(field && onToggle)
  const isActive = isSortable && sort.field === field
  const handleSort = () => {
    if (!isSortable) return
    onToggle(field)
  }

  return (
    <th className="px-4 py-3 text-left select-none">
      <div className="flex items-center gap-2 text-xs font-semibold text-gray-500 uppercase tracking-wider">
        <button
          type="button"
          className={`inline-flex items-center gap-1 ${
            isSortable ? 'text-gray-600 hover:text-gray-900' : 'cursor-default text-gray-400'
          }`}
          onClick={handleSort}
          disabled={!isSortable}
        >
          <span>{label}</span>
          {isActive && <span>{sort.direction === 'asc' ? '↑' : '↓'}</span>}
        </button>
        {filterKey ? (
          <ColumnFilterButton
            columnKey={filterKey}
            label={label}
            options={filterOptions}
            selectedItems={selectedFilters}
            customFilter={customFilter}
            onApply={(values) => onApplyFilter?.(filterKey, values)}
            onApplyCustomFilter={(payload) => onApplyCustomFilter?.(filterKey, payload)}
            disableSelectAll={(filterOptions?.length || 0) > 100}
          />
        ) : null}
      </div>
    </th>
  )
}
