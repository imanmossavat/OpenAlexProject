import { useEffect, useMemo, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import { Filter } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import {
  FILTER_OPERATION_DESCRIPTIONS,
  NUMBER_FILTER_OPERATIONS,
  TEXT_FILTER_OPERATIONS,
  getColumnType,
} from '../constants'

export default function ColumnFilterButton({
  columnKey,
  label,
  options = [],
  selectedItems = [],
  customFilter = null,
  onApply,
  onApplyCustomFilter,
  disableSelectAll = false,
}) {
  const [open, setOpen] = useState(false)
  const [searchValue, setSearchValue] = useState('')
  const [draftSelections, setDraftSelections] = useState(selectedItems)
  const [position, setPosition] = useState({ top: 0, left: 0 })
  const [startIndex, setStartIndex] = useState(0)
  const [mounted, setMounted] = useState(false)
  const [customDialogOpen, setCustomDialogOpen] = useState(false)
  const [customOperator, setCustomOperator] = useState('equals')
  const [customValue, setCustomValue] = useState('')
  const [customValueTo, setCustomValueTo] = useState('')
  const [customError, setCustomError] = useState('')
  const buttonRef = useRef(null)
  const popoverRef = useRef(null)
  const listRef = useRef(null)
  const selectAllRef = useRef(null)
  const columnType = getColumnType(columnKey)
  const availableOperations = columnType === 'number' ? NUMBER_FILTER_OPERATIONS : TEXT_FILTER_OPERATIONS

  const describeCustomFilter = (filter) => {
    if (!filter) return ''
    const operationLabel = FILTER_OPERATION_DESCRIPTIONS[filter.operator] || filter.operator
    if (filter.operator === 'between' || filter.operator === 'not_between') {
      const toValue = filter.valueTo ?? ''
      return `${label} ${operationLabel.toLowerCase()} ${filter.value} and ${toValue}`
    }
    return `${label} ${operationLabel.toLowerCase()} ${filter.value}`
  }

  useEffect(() => {
    setMounted(true)
  }, [])

  useEffect(() => {
    if (!open) return
    setDraftSelections(selectedItems || [])
    setSearchValue('')
    setStartIndex(0)
    if (listRef.current) listRef.current.scrollTop = 0
    if (buttonRef.current) {
      const rect = buttonRef.current.getBoundingClientRect()
      const width = 320
      const margin = 12
      const nextLeft = Math.min(Math.max(margin, rect.left), window.innerWidth - width - margin)
      const nextTop = Math.min(window.innerHeight - margin, rect.bottom + 8)
      setPosition({ top: nextTop, left: nextLeft })
    }
  }, [open, selectedItems])

  useEffect(() => {
    if (!open) return
    const handlePointerDown = (event) => {
      if (buttonRef.current?.contains(event.target) || popoverRef.current?.contains(event.target)) {
        return
      }
      setOpen(false)
    }
    const handleKeyDown = (event) => {
      if (event.key === 'Escape') setOpen(false)
    }
    const handleReposition = () => {
      if (!buttonRef.current) return
      const rect = buttonRef.current.getBoundingClientRect()
      const width = 320
      const margin = 12
      const nextLeft = Math.min(Math.max(margin, rect.left), window.innerWidth - width - margin)
      const nextTop = Math.min(window.innerHeight - margin, rect.bottom + 8)
      setPosition({ top: nextTop, left: nextLeft })
    }
    document.addEventListener('pointerdown', handlePointerDown)
    document.addEventListener('keydown', handleKeyDown)
    window.addEventListener('resize', handleReposition)
    window.addEventListener('scroll', handleReposition, true)
    return () => {
      document.removeEventListener('pointerdown', handlePointerDown)
      document.removeEventListener('keydown', handleKeyDown)
      window.removeEventListener('resize', handleReposition)
      window.removeEventListener('scroll', handleReposition, true)
    }
  }, [open])

  useEffect(() => {
    if (!customDialogOpen) return
    const defaultOperator = customFilter?.operator || availableOperations[0]?.value || 'equals'
    setCustomOperator(defaultOperator)
    setCustomValue(customFilter?.value ?? '')
    setCustomValueTo(customFilter?.valueTo ?? '')
    setCustomError('')
  }, [customDialogOpen, customFilter, availableOperations])

  const filteredOptions = useMemo(() => {
    if (!searchValue) return options || []
    const lower = searchValue.toLowerCase()
    return (options || []).filter((opt) => (opt.label || '').toLowerCase().includes(lower))
  }, [options, searchValue])

  const selectedValueSet = useMemo(
    () => new Set((draftSelections || []).map((item) => item.value)),
    [draftSelections]
  )

  const totalFiltered = filteredOptions.length
  const visibleCount = 12
  const sliceStart = Math.min(startIndex, Math.max(0, totalFiltered - visibleCount))
  const sliceEnd = Math.min(totalFiltered, sliceStart + visibleCount)
  const visibleOptions = filteredOptions.slice(sliceStart, sliceEnd)
  const paddingTop = sliceStart * 36
  const paddingBottom = Math.max(0, (totalFiltered - sliceEnd) * 36)
  const selectionCount = draftSelections?.length || 0
  const badgeCount = selectionCount + (customFilter ? 1 : 0)
  const allFilteredSelected = totalFiltered > 0 && filteredOptions.every((opt) => selectedValueSet.has(opt.value))
  const someFilteredSelected = filteredOptions.some((opt) => selectedValueSet.has(opt.value))
  const isBetweenOperation = customOperator === 'between' || customOperator === 'not_between'

  useEffect(() => {
    if (!selectAllRef.current) return
    selectAllRef.current.indeterminate = !disableSelectAll && someFilteredSelected && !allFilteredSelected
  }, [disableSelectAll, someFilteredSelected, allFilteredSelected])

  const toggleOption = (option) => {
    setDraftSelections((prev) => {
      const exists = (prev || []).some((item) => item.value === option.value)
      if (exists) {
        return prev.filter((item) => item.value !== option.value)
      }
      return [...prev, { value: option.value, label: option.label, meta: option.meta || null }]
    })
  }

  const handleSelectAll = (event) => {
    if (disableSelectAll) return
    const checked = event.target.checked
    setDraftSelections((prev) => {
      const map = new Map((prev || []).map((item) => [item.value, item]))
      if (checked) {
        filteredOptions.forEach((option) => {
          if (!map.has(option.value)) {
            map.set(option.value, {
              value: option.value,
              label: option.label,
              meta: option.meta || null,
            })
          }
        })
      } else {
        filteredOptions.forEach((option) => map.delete(option.value))
      }
      return Array.from(map.values())
    })
  }

  const handleApplySelections = () => {
    onApply?.(draftSelections)
    setOpen(false)
  }

  const handleClearSelections = () => {
    onApply?.([])
    setOpen(false)
  }

  const handleClearCustom = () => {
    onApplyCustomFilter?.(null)
  }

  const handleCustomSave = () => {
    if (!customOperator) {
      setCustomError('Select an operation')
      return
    }
    const trimmedValue = `${customValue}`.trim()
    if (!trimmedValue) {
      setCustomError('Enter a value')
      return
    }
    if (columnType === 'number' && Number.isNaN(Number(trimmedValue))) {
      setCustomError('Enter a valid number')
      return
    }
    let trimmedValueTo = ''
    if (isBetweenOperation) {
      trimmedValueTo = `${customValueTo}`.trim()
      if (!trimmedValueTo) {
        setCustomError('Enter both values')
        return
      }
      if (columnType === 'number' && Number.isNaN(Number(trimmedValueTo))) {
        setCustomError('Enter a valid range')
        return
      }
    }
    onApplyCustomFilter?.({
      operator: customOperator,
      value: trimmedValue,
      valueTo: isBetweenOperation ? trimmedValueTo : null,
    })
    setCustomDialogOpen(false)
  }

  const listContent =
    visibleOptions.length === 0 ? (
      <div className="text-center text-sm text-gray-500 py-4">No values match this search.</div>
    ) : (
      <div style={{ paddingTop, paddingBottom }}>
        {visibleOptions.map((option) => (
          <label
            key={option.value}
            className="flex items-center justify-between gap-2 px-2 py-1.5 text-sm text-gray-700"
          >
            <div className="flex items-center gap-2 min-w-0">
              <input
                type="checkbox"
                className="rounded border-gray-300 text-gray-900 focus:ring-gray-900"
                checked={selectedValueSet.has(option.value)}
                onChange={() => toggleOption(option)}
              />
              <span className="truncate">{option.label}</span>
              {option.meta?.type && (
                <span className="text-[10px] uppercase text-gray-400 rounded-full border border-gray-200 px-2 py-0.5">
                  {option.meta.type}
                </span>
              )}
            </div>
            <span className="text-xs text-gray-400">
              {option.count?.toLocaleString?.() || option.count || 0}
            </span>
          </label>
        ))}
      </div>
    )

  if (!mounted) {
    return (
      <button
        type="button"
        ref={buttonRef}
        aria-label={`Filter ${label}`}
        className="inline-flex items-center justify-center rounded-full border border-gray-200 p-1 text-gray-500 hover:bg-gray-100"
        onClick={() => setOpen((prev) => !prev)}
      >
        <Filter className="w-3.5 h-3.5" />
      </button>
    )
  }

  return (
    <>
      <div className="relative">
        <button
          type="button"
          ref={buttonRef}
          aria-label={`Filter ${label}`}
          className={`relative inline-flex items-center justify-center rounded-full border p-1 transition ${
            badgeCount ? 'bg-gray-900 text-white border-gray-900' : 'border-gray-200 text-gray-500 hover:bg-gray-100'
          }`}
          onClick={() => setOpen((prev) => !prev)}
        >
          <Filter className="w-3.5 h-3.5" />
          {badgeCount > 0 && (
            <span className="absolute -top-1 -right-1 rounded-full bg-white text-gray-900 text-[10px] font-semibold px-1">
              {badgeCount}
            </span>
          )}
        </button>
        {open &&
          createPortal(
            <div
              ref={popoverRef}
              className="fixed z-50 w-80 rounded-3xl border border-gray-200 bg-white shadow-2xl p-4 space-y-3"
              style={{ top: position.top, left: position.left }}
            >
              <div className="flex items-center justify-between text-xs text-gray-500">
                <span className="font-semibold text-gray-900">{label} filters</span>
                <span>{selectionCount} selected</span>
              </div>
              <input
                type="text"
                className="w-full rounded-full border border-gray-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-gray-900"
                placeholder={`Search ${label.toLowerCase()}`}
                value={searchValue}
                onChange={(e) => setSearchValue(e.target.value)}
              />
              <div className="flex items-center justify-between text-xs text-gray-600">
                <label className="inline-flex items-center gap-2">
                  <input
                    type="checkbox"
                    ref={selectAllRef}
                    className="rounded border-gray-300 text-gray-900 focus:ring-gray-900"
                    disabled={disableSelectAll || filteredOptions.length === 0}
                    checked={!disableSelectAll && filteredOptions.length > 0 && allFilteredSelected}
                    onChange={handleSelectAll}
                  />
                  <span>Select all</span>
                </label>
                {disableSelectAll && (
                  <span className="text-[11px] text-gray-400">Disabled for large lists</span>
                )}
              </div>
              <div
                ref={listRef}
                className="max-h-60 overflow-y-auto border border-gray-100 rounded-2xl"
                onScroll={(event) => {
                  const newIndex = Math.floor(event.currentTarget.scrollTop / 36)
                  if (newIndex !== startIndex) setStartIndex(newIndex)
                }}
              >
                {listContent}
              </div>
              {customFilter ? (
                <div className="rounded-2xl bg-gray-50 px-3 py-2 text-[11px] text-gray-600 flex items-center justify-between gap-3">
                  <span className="truncate">{describeCustomFilter(customFilter)}</span>
                  <button
                    type="button"
                    className="text-gray-500 hover:text-gray-900 font-semibold"
                    onClick={handleClearCustom}
                  >
                    Clear
                  </button>
                </div>
              ) : null}
              <button
                type="button"
                className="text-xs text-gray-600 underline decoration-dotted hover:text-gray-900"
                onClick={() => setCustomDialogOpen(true)}
              >
                Custom filter…
              </button>
              <div className="flex items-center justify-between gap-3 pt-2 border-t border-gray-100">
                <Button
                  type="button"
                  variant="outline"
                  className="rounded-full px-4 text-xs"
                  onClick={handleClearSelections}
                >
                  Clear
                </Button>
                <Button
                  type="button"
                  className="rounded-full px-4 text-xs bg-gray-900 text-white"
                  onClick={handleApplySelections}
                >
                  Apply
                </Button>
              </div>
            </div>,
            document.body
          )}
      </div>
      <Dialog open={customDialogOpen} onOpenChange={setCustomDialogOpen}>
        <DialogContent className="sm:max-w-md bg-white p-6 rounded-3xl border-0 shadow-2xl">
          <DialogHeader className="pb-2">
            <DialogTitle>Custom filter for {label}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 text-sm text-gray-600">
            <div className="text-xs uppercase tracking-wider text-gray-500">
              Show items where: <span className="text-gray-900 normal-case">{label.toLowerCase()}</span>
            </div>
            <div>
              <label className="text-xs uppercase tracking-wider text-gray-500 mb-1 block">Operation</label>
              <Select
                value={customOperator}
                onValueChange={(value) => {
                  setCustomOperator(value)
                  if (value !== 'between' && value !== 'not_between') {
                    setCustomValueTo('')
                  }
                }}
              >
                <SelectTrigger className="w-full rounded-full border border-gray-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-gray-900">
                  <SelectValue placeholder="Choose operation" />
                </SelectTrigger>
                <SelectContent className="rounded-2xl border border-gray-200 bg-white shadow-lg">
                  {availableOperations.map((operation) => (
                    <SelectItem key={operation.value} value={operation.value}>
                      {operation.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className={isBetweenOperation ? 'grid grid-cols-1 sm:grid-cols-2 gap-3' : ''}>
              <div>
                <label className="text-xs uppercase tracking-wider text-gray-500 mb-1 block">
                  {columnType === 'number' ? 'Value' : 'Text'}
                </label>
                <Input
                  type={columnType === 'number' ? 'number' : 'text'}
                  value={customValue}
                  onChange={(e) => setCustomValue(e.target.value)}
                  placeholder={columnType === 'number' ? 'e.g. 2020' : 'e.g. Nature'}
                  className="rounded-full"
                />
              </div>
              {isBetweenOperation ? (
                <div>
                  <label className="text-xs uppercase tracking-wider text-gray-500 mb-1 block">And</label>
                  <Input
                    type={columnType === 'number' ? 'number' : 'text'}
                    value={customValueTo}
                    onChange={(e) => setCustomValueTo(e.target.value)}
                    placeholder={columnType === 'number' ? 'e.g. 2024' : 'e.g. Sensors'}
                    className="rounded-full"
                  />
                </div>
              ) : null}
            </div>
            {customError && <p className="text-xs text-red-600">{customError}</p>}
            <div className="flex justify-end gap-3 pt-2">
              <Button
                type="button"
                variant="outline"
                className="rounded-full px-4 text-xs"
                onClick={() => setCustomDialogOpen(false)}
              >
                Cancel
              </Button>
              <Button
                type="button"
                className="rounded-full px-4 text-xs bg-gray-900 text-white"
                onClick={handleCustomSave}
              >
                OK
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </>
  )
}
