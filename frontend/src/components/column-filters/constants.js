export const TEXT_FILTER_OPERATIONS = [
  { value: 'equals', label: 'Equals' },
  { value: 'not_equals', label: 'Does not equal' },
  { value: 'begins_with', label: 'Begins with' },
  { value: 'not_begins_with', label: 'Does not begin with' },
  { value: 'ends_with', label: 'Ends with' },
  { value: 'not_ends_with', label: 'Does not end with' },
  { value: 'contains', label: 'Contains' },
  { value: 'not_contains', label: 'Does not contain' },
]

export const NUMBER_FILTER_OPERATIONS = [
  { value: 'equals', label: 'Equals' },
  { value: 'not_equals', label: 'Does not equal' },
  { value: 'greater_than', label: 'Is greater than' },
  { value: 'greater_than_or_equal', label: 'Is greater than or equal to' },
  { value: 'less_than', label: 'Is less than' },
  { value: 'less_than_or_equal', label: 'Is less than or equal to' },
  { value: 'between', label: 'Is between' },
  { value: 'not_between', label: 'Is not between' },
]

export const FILTER_OPERATION_DESCRIPTIONS = TEXT_FILTER_OPERATIONS.concat(
  NUMBER_FILTER_OPERATIONS
).reduce((acc, item) => {
  acc[item.value] = item.label
  return acc
}, {})

export const getColumnType = (columnKey) => (columnKey === 'year' ? 'number' : 'text')
