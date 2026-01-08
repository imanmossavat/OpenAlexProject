import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { AlertCircle, ArrowLeft, CheckCircle2, ExternalLink, Shield } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import apiClient from '@/shared/api/client'
import { endpoints } from '@/shared/api/endpoints'

export default function IntegrationsSettingsPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const focusProvider = searchParams.get('provider')

  const openAlexRef = useRef(null)
  const zoteroRef = useRef(null)

  const [settings, setSettings] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [flashMessage, setFlashMessage] = useState(null)
  const [saving, setSaving] = useState({ openalex: false, zotero: false })

  const [openAlexEmail, setOpenAlexEmail] = useState('')
  const [zoteroLibraryId, setZoteroLibraryId] = useState('')
  const [zoteroLibraryType, setZoteroLibraryType] = useState('user')
  const [zoteroApiKey, setZoteroApiKey] = useState('')
  const [clearStoredApiKey, setClearStoredApiKey] = useState(false)

  const fetchSettings = useCallback(async () => {
    setLoading(true)
    const res = await apiClient('GET', `${endpoints.settings}/integrations`)
    if (res.error) {
      setError(res.error)
    } else {
      setSettings(res.data)
      setError(null)
    }
    setLoading(false)
  }, [])

  useEffect(() => {
    fetchSettings()
  }, [fetchSettings])

  useEffect(() => {
    if (!settings) return
    setOpenAlexEmail(settings.openalex?.email || '')
    setZoteroLibraryId(settings.zotero?.library_id || '')
    setZoteroLibraryType(settings.zotero?.library_type || 'user')
    setZoteroApiKey('')
    setClearStoredApiKey(false)
  }, [settings])

  useEffect(() => {
    if (loading) return
    const target =
      focusProvider === 'zotero'
        ? zoteroRef.current
        : focusProvider === 'openalex'
        ? openAlexRef.current
        : null

    if (target) {
      target.scrollIntoView({ behavior: 'smooth', block: 'start' })
      target.classList.add('ring-2', 'ring-purple-500')
      const timeout = setTimeout(() => target.classList.remove('ring-2', 'ring-purple-500'), 1600)
      return () => clearTimeout(timeout)
    }
  }, [focusProvider, loading])

  const providerStatus = useMemo(() => {
    if (!settings) return { openalex: null, zotero: null }
    return {
      openalex: settings.openalex?.configured,
      zotero: settings.zotero?.configured,
    }
  }, [settings])

  const saveOpenAlex = async () => {
    if (!openAlexEmail) {
      setError('OpenAlex email is required.')
      return
    }
    setSaving((prev) => ({ ...prev, openalex: true }))
    const res = await apiClient('PUT', `${endpoints.settings}/openalex`, { email: openAlexEmail })
    setSaving((prev) => ({ ...prev, openalex: false }))
    if (res.error) {
      setError(res.error)
      return
    }
    setSettings(res.data)
    setFlashMessage('OpenAlex settings saved.')
    setTimeout(() => setFlashMessage(null), 4000)
  }

  const saveZotero = async () => {
    if (!zoteroLibraryId) {
      setError('Zotero library ID is required.')
      return
    }
    setSaving((prev) => ({ ...prev, zotero: true }))
    const payload = {
      library_id: zoteroLibraryId,
      library_type: zoteroLibraryType,
    }
    const trimmedKey = zoteroApiKey.trim()
    if (clearStoredApiKey) {
      payload.api_key = ''
    } else if (trimmedKey) {
      payload.api_key = trimmedKey
    }

    const res = await apiClient('PUT', `${endpoints.settings}/zotero`, payload)
    setSaving((prev) => ({ ...prev, zotero: false }))
    if (res.error) {
      setError(res.error)
      return
    }
    setSettings(res.data)
    setFlashMessage('Zotero settings saved.')
    setZoteroApiKey('')
    setClearStoredApiKey(false)
    setTimeout(() => setFlashMessage(null), 4000)
  }

  const handleClearApiKey = () => {
    setZoteroApiKey('')
    setClearStoredApiKey(true)
  }

  return (
    <div className="min-h-[calc(100vh-160px)] bg-white">
      <div className="max-w-5xl mx-auto px-6 py-10 space-y-6">
        <div className="flex items-center gap-4">
          <Button
            variant="outline"
            className="rounded-full shadow-sm hover:shadow-md transition"
            onClick={() => navigate(-1)}
          >
            <ArrowLeft className="w-4 h-4 mr-2" /> Back
          </Button>

          <div>
            <p className="text-xs uppercase tracking-[0.3em] text-gray-500 mb-1">Integrations</p>
            <h1 className="text-3xl font-semibold text-gray-900">Connect your data sources</h1>
            <p className="text-gray-500 text-sm mt-2">
              These credentials are stored securely in the API .env file. Update them anytime to enable polite OpenAlex
              requests or Zotero imports.
            </p>
          </div>
        </div>

        {error && (
          <div className="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 flex items-center gap-2 shadow-sm">
            <AlertCircle className="w-4 h-4" />
            {error}
          </div>
        )}

        {flashMessage && (
          <div className="rounded-2xl border border-green-200 bg-green-50 px-4 py-3 text-sm text-green-700 flex items-center gap-2 shadow-sm">
            <CheckCircle2 className="w-4 h-4" />
            {flashMessage}
          </div>
        )}

        {/* OPENALEX */}
        <section ref={openAlexRef} className="border border-gray-200 rounded-3xl p-6 shadow-md bg-white">
          <div className="flex items-center justify-between mb-4">
            <div>
              <p className="text-xs uppercase tracking-[0.3em] text-gray-500 mb-1">OpenAlex</p>
              <h2 className="text-2xl font-semibold text-gray-900">Polite API usage</h2>
              <p className="text-sm text-gray-500">Provide a contact email so OpenAlex keeps generous rate limits.</p>
            </div>
            <StatusBadge healthy={providerStatus.openalex} />
          </div>

          {loading ? (
            <div className="text-sm text-gray-500">Loading current settings…</div>
          ) : (
            <div className="space-y-4">
              <div>
                <Label className="text-xs uppercase tracking-wider text-gray-500 mb-1 block">Contact email</Label>
                <Input
                  type="email"
                  value={openAlexEmail}
                  onChange={(e) => setOpenAlexEmail(e.target.value)}
                  placeholder="you@example.com"
                  className="rounded-full shadow-sm"
                />
              </div>

              <div className="flex items-center justify-between">
                <p className="text-xs text-gray-500">This email is shared with OpenAlex on every polite API request.</p>
                <Button
                  className="rounded-full bg-gray-900 text-white hover:bg-gray-800 disabled:opacity-60"
                  onClick={saveOpenAlex}
                  disabled={saving.openalex}
                >
                  {saving.openalex ? 'Saving…' : 'Save changes'}
                </Button>
              </div>
            </div>
          )}
        </section>

        {/* ZOTERO */}
        <section ref={zoteroRef} className="border border-gray-200 rounded-3xl p-6 shadow-md bg-white">
          <div className="flex items-center justify-between mb-4">
            <div>
              <p className="text-xs uppercase tracking-[0.3em] text-gray-500 mb-1">Zotero</p>
              <h2 className="text-2xl font-semibold text-gray-900">Library access</h2>
              <p className="text-sm text-gray-500">
                Provide a read-enabled API key and library details so we can browse your Zotero collections.
              </p>
            </div>
            <StatusBadge healthy={providerStatus.zotero} />
          </div>

          {loading ? (
            <div className="text-sm text-gray-500">Loading current settings…</div>
          ) : (
            <div className="space-y-5">
              <div className="grid md:grid-cols-2 gap-4">
                <div>
                  <Label className="text-xs uppercase tracking-wider text-gray-500 mb-1 block">Library ID</Label>
                  <Input
                    value={zoteroLibraryId}
                    onChange={(e) => setZoteroLibraryId(e.target.value)}
                    placeholder="e.g. 1234567"
                    className="rounded-full shadow-sm"
                  />
                </div>

                <div>
                  <Label className="text-xs uppercase tracking-wider text-gray-500 mb-1 block">Library type</Label>
                  <div className="flex gap-2">
                    {['user', 'group'].map((type) => (
                      <button
                        key={type}
                        type="button"
                        className={`flex-1 rounded-full border px-4 py-2 text-sm transition ${
                          zoteroLibraryType === type
                            ? 'bg-gray-900 text-white border-gray-900 shadow-sm'
                            : 'border-gray-200 text-gray-600 hover:border-gray-400 hover:shadow-sm'
                        }`}
                        onClick={() => setZoteroLibraryType(type)}
                      >
                        {type === 'user' ? 'Personal library' : 'Group library'}
                      </button>
                    ))}
                  </div>
                </div>
              </div>

              <div>
                <Label className="text-xs uppercase tracking-wider text-gray-500 mb-1 block">API key</Label>
                <Input
                  type="password"
                  value={zoteroApiKey}
                  onChange={(e) => {
                    setZoteroApiKey(e.target.value)
                    setClearStoredApiKey(false)
                  }}
                  placeholder={
                    settings?.zotero?.has_api_key
                      ? 'Stored securely (enter a new key to replace)'
                      : 'Zotero API key'
                  }
                  className="rounded-full shadow-sm placeholder:text-gray-400 placeholder:opacity-80"
                />

                <div className="flex items-center justify-between mt-2">
                  <p className="text-xs text-gray-500">
                    {settings?.zotero?.has_api_key
                      ? 'An API key is stored securely. Leave blank to keep it, or enter a new key to overwrite.'
                      : 'Paste a read-only API key created for this app.'}
                  </p>

                  <Button
                    type="button"
                    variant="ghost"
                    className="text-xs text-gray-600 hover:text-gray-900"
                    onClick={handleClearApiKey}
                    disabled={!settings?.zotero?.has_api_key}
                  >
                    Remove stored key
                  </Button>
                </div>
              </div>

              <ZoteroGuide />

              <div className="flex items-center justify-between">
                <p className="text-xs text-gray-500">Use the same credentials you rely on inside Zotero.</p>
                <Button
                  className="rounded-full bg-gray-900 text-white hover:bg-gray-800 disabled:opacity-60"
                  onClick={saveZotero}
                  disabled={saving.zotero}
                >
                  {saving.zotero ? 'Saving…' : 'Save changes'}
                </Button>
              </div>
            </div>
          )}
        </section>
      </div>
    </div>
  )
}

function StatusBadge({ healthy }) {
  if (healthy === null) return null
  return healthy ? (
    <span className="inline-flex items-center gap-1 rounded-full bg-green-50 px-3 py-1 text-xs font-medium text-green-700">
      <CheckCircle2 className="w-4 h-4" /> Configured
    </span>
  ) : (
    <span className="inline-flex items-center gap-1 rounded-full bg-amber-50 px-3 py-1 text-xs font-medium text-amber-700">
      <Shield className="w-4 h-4" /> Needs setup
    </span>
  )
}

function ZoteroGuide() {
  return (
    <div className="rounded-2xl border border-gray-200 bg-gray-50 px-4 py-3 text-sm text-gray-700 shadow-sm">
      <p className="font-semibold text-gray-800 mb-2">Need a hand?</p>
      <ol className="list-decimal list-inside space-y-1 text-gray-600 text-sm">
        <li>
          Visit{' '}
          <a
            href="https://www.zotero.org/settings/keys"
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-1 text-purple-600 hover:text-purple-700"
          >
            zotero.org/settings/keys <ExternalLink className="w-3 h-3" />
          </a>
        </li>
        <li>Create a new key with read access to the library you need.</li>
        <li>Copy the “Library ID” from the top of that page.</li>
        <li>Paste the ID and API key here, then save your changes.</li>
      </ol>
    </div>
  )
}
