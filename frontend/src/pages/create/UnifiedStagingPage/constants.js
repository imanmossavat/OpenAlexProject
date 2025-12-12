import {
  FILTER_OPERATION_DESCRIPTIONS,
  NUMBER_FILTER_OPERATIONS,
  TEXT_FILTER_OPERATIONS,
  getColumnType,
} from '@/components/column-filters/constants'

export const WORKFLOW_STEPS = ['Add', 'Stage', 'Match', 'Library']

export const EDITABLE_FIELDS = ['title', 'authors', 'year', 'venue', 'doi', 'url', 'abstract']

export const DEFAULT_GROBID_STATUS = { checked: false, available: true, message: null }

export const FILTERABLE_COLUMNS = [
  { key: 'title', label: 'Title' },
  { key: 'authors', label: 'Authors' },
  { key: 'year', label: 'Year' },
  { key: 'venue', label: 'Venue' },
  { key: 'identifier', label: 'Identifiers' },
]

export const COLUMN_QUERY_MAP = {
  title: 'title_values',
  authors: 'author_values',
  year: 'year_values',
  venue: 'venue_values',
  identifier: 'identifier_values',
}

export const createColumnState = () =>
  FILTERABLE_COLUMNS.reduce((acc, { key }) => {
    acc[key] = []
    return acc
  }, {})

export const createColumnCustomState = () =>
  FILTERABLE_COLUMNS.reduce((acc, { key }) => {
    acc[key] = null
    return acc
  }, {})

export const createDefaultFilters = () => ({
  sources: [],
  yearMin: '',
  yearMax: '',
  title: '',
  venue: '',
  author: '',
  keyword: '',
  doi: 'all',
  retraction: 'all',
  selectedOnly: false,
})

export {
  TEXT_FILTER_OPERATIONS,
  NUMBER_FILTER_OPERATIONS,
  FILTER_OPERATION_DESCRIPTIONS,
  getColumnType,
}
