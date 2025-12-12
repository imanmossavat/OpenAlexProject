const SESSION_ID_KEY = 'session_id'
const SESSION_USE_CASE_KEY = 'session_use_case'

export function getSessionId() {
  try {
    return typeof window !== 'undefined' ? localStorage.getItem(SESSION_ID_KEY) : null
  } catch {
    return null
  }
}

export function setSessionId(id, options = {}) {
  try {
    if (typeof window === 'undefined') return
    if (id) {
      localStorage.setItem(SESSION_ID_KEY, id)
      if (options.useCase) {
        localStorage.setItem(SESSION_USE_CASE_KEY, options.useCase)
      }
    }
  } catch {}
}

export function getSessionUseCase() {
  try {
    return typeof window !== 'undefined' ? localStorage.getItem(SESSION_USE_CASE_KEY) : null
  } catch {
    return null
  }
}

export function clearSession() {
  try {
    if (typeof window !== 'undefined') {
      localStorage.removeItem(SESSION_ID_KEY)
      localStorage.removeItem(SESSION_USE_CASE_KEY)
    }
  } catch {}
}

export function hydrateSessionFromQuery(searchString) {
  try {
    const search = searchString || (typeof window !== 'undefined' ? window.location.search : '')
    const params = new URLSearchParams(search)
    const sid = params.get('sid')
    if (sid) setSessionId(sid)
    return sid
  } catch {
    return null
  }
}

export default { getSessionId, setSessionId, getSessionUseCase, clearSession, hydrateSessionFromQuery }

