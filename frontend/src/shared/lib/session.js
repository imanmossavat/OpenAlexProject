export function getSessionId() {
  try {
    return typeof window !== 'undefined' ? localStorage.getItem('session_id') : null
  } catch {
    return null
  }
}

export function setSessionId(id) {
  try {
    if (typeof window !== 'undefined' && id) localStorage.setItem('session_id', id)
  } catch {}
}

export function clearSession() {
  try {
    if (typeof window !== 'undefined') localStorage.removeItem('session_id')
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

export default { getSessionId, setSessionId, clearSession, hydrateSessionFromQuery }

