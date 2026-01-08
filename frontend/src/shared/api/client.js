import config from '@/shared/config/env'
import { endpoints } from '@/shared/api/endpoints'
import { clearSession, getSessionUseCase, setSessionId } from '@/shared/lib/session'

function buildUrl(base, endpoint, query) {
  const baseUrl = String(base || '').replace(/\/+$/, '')
  const end = (endpoint || '').toString()
  const path = end.startsWith('/') ? end : `/${end}`
  const url = new URL(baseUrl + path)
  if (query && typeof query === 'object') {
    Object.entries(query).forEach(([key, val]) => {
      if (val === undefined || val === null) return
      if (Array.isArray(val)) {
        val.forEach((v) => url.searchParams.append(key, String(v)))
      } else {
        url.searchParams.set(key, String(val))
      }
    })
  }
  return url.toString()
}

const LIBRARY_CREATION_USE_CASE = 'library_creation'
const SESSION_NOT_FOUND_PATTERN = /session\b.*not found/i
let librarySessionRecovery = null

function shouldRestartLibrarySession(status, errorMessage) {
  if (status !== 404) return false
  if (getSessionUseCase() !== LIBRARY_CREATION_USE_CASE) return false
  return SESSION_NOT_FOUND_PATTERN.test(String(errorMessage || ''))
}

function redirectToLibraryCreationStart() {
  if (typeof window === 'undefined') return
  const target = '/create/library-start'
  if (window.location.pathname === target) {
    window.location.reload()
  } else {
    window.location.href = target
  }
}

async function restartLibrarySession() {
  if (typeof window === 'undefined') return null
  if (librarySessionRecovery) return librarySessionRecovery

  librarySessionRecovery = (async () => {
    try {
      clearSession()
      const startUrl = buildUrl(config.apiUrl, `${endpoints.seedsSession}/start`)
      const response = await fetch(startUrl, {
        method: 'POST',
        headers: {
          Accept: 'application/json',
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ use_case: LIBRARY_CREATION_USE_CASE }),
      })
      if (!response.ok) return null
      let data = null
      try {
        data = await response.json()
      } catch (_) {
        data = null
      }
      const newSessionId = data?.session_id
      if (newSessionId) {
        setSessionId(newSessionId, { useCase: LIBRARY_CREATION_USE_CASE })
        setTimeout(redirectToLibraryCreationStart, 0)
      }
      return newSessionId
    } catch (_) {
      return null
    } finally {
      librarySessionRecovery = null
    }
  })()

  return librarySessionRecovery
}

export default async function apiClient(method = 'GET', endpoint = '', body, options = {}) {
  const { headers: hdrs = {}, query, signal, ...rest } = options || {}
  const url = buildUrl(config.apiUrl, endpoint, query)

  const upperMethod = String(method).toUpperCase()
  const isGetLike = upperMethod === 'GET' || upperMethod === 'HEAD'

  const headers = {
    Accept: 'application/json',
    ...hdrs,
  }

  let payload
  if (!isGetLike && body !== undefined && body !== null) {
    const isFormLike =
      (typeof FormData !== 'undefined' && body instanceof FormData) ||
      (typeof URLSearchParams !== 'undefined' && body instanceof URLSearchParams) ||
      (typeof Blob !== 'undefined' && body instanceof Blob) ||
      (typeof File !== 'undefined' && body instanceof File)

    if (!isFormLike) {
      const hasContentType = headers['Content-Type'] || headers['content-type']
      if (!hasContentType) headers['Content-Type'] = 'application/json'
      const ct = (headers['Content-Type'] || headers['content-type'] || '').toString()
      payload = ct.includes('application/json') && typeof body !== 'string' ? JSON.stringify(body) : body
    } else {
      // Let the browser set Content-Type with proper boundaries for form data
      payload = body
    }
  }

  try {
    const response = await fetch(url, {
      method: upperMethod,
      headers,
      body: isGetLike ? undefined : payload,
      signal,
      ...rest,
    })

    const contentType = response.headers.get('content-type') || ''
    let data = null
    if (response.status !== 204) {
      if (contentType.includes('application/json')) {
        try {
          data = await response.json()
        } catch (_) {
          data = null
        }
      } else {
        try {
          data = await response.text()
        } catch (_) {
          data = null
        }
      }
    }

    if (!response.ok) {
      const errorMessage =
        (data && (data.detail || data.message || data.error)) || `${response.status} ${response.statusText}`
      console.error('API error:', { url, status: response.status, error: errorMessage, data })
      if (shouldRestartLibrarySession(response.status, errorMessage)) {
        restartLibrarySession()
      }
      return { data: null, error: errorMessage, loading: false }
    }

    return { data, error: null, loading: false }
  } catch (err) {
    const message = (err && err.message) || 'Network error'
    console.error('API network error:', { url, error: message })
    return { data: null, error: message, loading: false }
  }
}
