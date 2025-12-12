export const CATALOG_FILTERABLE_COLUMNS = [
  { key: 'title', label: 'Title' },
  { key: 'authors', label: 'Authors' },
  { key: 'year', label: 'Year' },
  { key: 'venue', label: 'Venue' },
  { key: 'identifier', label: 'DOI' },
]

export const createCatalogColumnState = () =>
  CATALOG_FILTERABLE_COLUMNS.reduce((acc, { key }) => {
    acc[key] = []
    return acc
  }, {})

export const createCatalogColumnCustomState = () =>
  CATALOG_FILTERABLE_COLUMNS.reduce((acc, { key }) => {
    acc[key] = null
    return acc
  }, {})

export const CATALOG_COLUMN_QUERY_MAP = {
  title: 'title_values',
  authors: 'author_values',
  year: 'year_values',
  venue: 'venue_values',
  identifier: 'identifier_filters',
}

export const CATALOG_ANNOTATION_MARKS = [
  { value: 'standard', label: 'Standard' },
  { value: 'good', label: 'Good' },
  { value: 'neutral', label: 'Neutral' },
  { value: 'bad', label: 'Bad' },
]

export const CATALOG_ANNOTATION_MARK_VALUES = CATALOG_ANNOTATION_MARKS.map((item) => item.value)
