const STORAGE_KEY = 'author-topic-selected-author'
const RESULT_KEY = 'author-topic-last-result'

export function saveSelectedAuthor(author) {
  if (!author) return
  try {
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(author))
  } catch (err) {
    console.error('Failed to save author selection', err)
  }
}

export function loadSelectedAuthor() {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY)
    if (!raw) return null
    return JSON.parse(raw)
  } catch (err) {
    console.error('Failed to load author selection', err)
    return null
  }
}

export function clearSelectedAuthor() {
  try {
    sessionStorage.removeItem(STORAGE_KEY)
  } catch (err) {
    console.error('Failed to clear author selection', err)
  }
}

export function saveAuthorTopicResult(result) {
  if (!result) return
  try {
    sessionStorage.setItem(RESULT_KEY, JSON.stringify(result))
  } catch (err) {
    console.error('Failed to save author topic result', err)
  }
}

export function loadAuthorTopicResult() {
  try {
    const raw = sessionStorage.getItem(RESULT_KEY)
    if (!raw) return null
    return JSON.parse(raw)
  } catch (err) {
    console.error('Failed to load author topic result', err)
    return null
  }
}

export function clearAuthorTopicResult() {
  try {
    sessionStorage.removeItem(RESULT_KEY)
  } catch (err) {
    console.error('Failed to clear author topic result', err)
  }
}
