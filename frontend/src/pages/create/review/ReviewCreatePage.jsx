import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import Stepper from '@/components/Stepper'
import apiClient from '@/shared/api/client'
import { endpoints } from '@/shared/api/endpoints'
import { getSessionId, getSessionUseCase, hydrateSessionFromQuery, clearSession } from '@/shared/lib/session'
import { isAbsolutePath } from '@/pages/libraries/utils'

export default function ReviewCreatePage() {
  const navigate = useNavigate()
  const steps = ['Add', 'Stage', 'Match', 'Library']
  const [sessionId, setSessionId] = useState(null)
  const [preview, setPreview] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [creating, setCreating] = useState(false)
  const [sessionUseCase] = useState(() => getSessionUseCase())
  const isEditMode = sessionUseCase === 'library_edit'
  const [editMode, setEditMode] = useState('update')
  const [duplicatePath, setDuplicatePath] = useState('')
  const [duplicateName, setDuplicateName] = useState('')
  const [duplicateDescription, setDuplicateDescription] = useState('')
  const [duplicatePathDirty, setDuplicatePathDirty] = useState(false)

  const duplicatePathPlaceholder = useMemo(() => {
    if (!preview?.path) return '/absolute/path/to/library-copy'
    return derivePathFromName(preview.path, preview.name ? `${preview.name} (Copy)` : 'Library Copy')
  }, [preview])

  const duplicatePathValid = useMemo(
    () => !!duplicatePath && isAbsolutePath(duplicatePath),
    [duplicatePath]
  )

  useEffect(() => {
    const sid = getSessionId() || hydrateSessionFromQuery()
    if (!sid) { navigate('/'); return }
    setSessionId(sid)
  }, [navigate])

  useEffect(() => {
    if (!sessionId) return
    ;(async () => {
      const pv = await apiClient('GET', `${endpoints.library}/${sessionId}/preview`)
      if (pv.error) setError(pv.error)
      else setPreview(pv.data)
      setLoading(false)
    })()
  }, [sessionId])

  useEffect(() => {
    if (!isEditMode || !preview) return
    const defaultName = preview.name ? `${preview.name} (Copy)` : 'Library Copy'
    setDuplicateName((prev) => (prev ? prev : defaultName))
    setDuplicateDescription((prev) => (prev ? prev : preview.description || ''))
    const defaultPath = derivePathFromName(preview.path, defaultName)
    setDuplicatePath((prev) => (prev ? prev : defaultPath))
    setDuplicatePathDirty(false)
  }, [isEditMode, preview])

  useEffect(() => {
    if (!isEditMode || editMode !== 'duplicate' || duplicatePathDirty || !preview) return
    const autoPath = derivePathFromName(preview.path, duplicateName)
    if (autoPath) setDuplicatePath(autoPath)
  }, [duplicateName, duplicatePathDirty, editMode, isEditMode, preview])

  const createLibrary = async () => {
    if (!sessionId) return
    setCreating(true)
    setError(null)
    const res = await apiClient('POST', `${endpoints.library}/${sessionId}/create`)
    if (res.error) {
      setError(res.error)
      setCreating(false)
    } else {
      clearSession()
      navigate('/')
    }
  }

  const commitEdits = async () => {
    if (!sessionId) return
    if (editMode === 'duplicate' && (!duplicatePath.trim() || !duplicatePathValid)) {
      setError('Provide an absolute path for the duplicated library.')
      return
    }
    setCreating(true)
    setError(null)
    const payload = { mode: editMode }
    if (editMode === 'duplicate') {
      payload.duplicate_path = duplicatePath.trim()
      if (duplicateName.trim()) payload.duplicate_name = duplicateName.trim()
      if (duplicateDescription.trim()) payload.duplicate_description = duplicateDescription.trim()
    }
    const res = await apiClient('POST', `${endpoints.library}/${sessionId}/edit/commit`, payload)
    if (res.error) {
      setError(res.error)
      setCreating(false)
      return
    }
    clearSession()
    navigate('/libraries')
  }

  const handlePrimaryAction = () => {
    if (isEditMode) {
      commitEdits()
    } else {
      createLibrary()
    }
  }

  const primaryLabel = isEditMode
    ? editMode === 'duplicate'
      ? 'Save as new library'
      : 'Apply changes'
    : 'Create Library'

  const handleEditModeChange = (value) => {
    setEditMode(value)
    setDuplicatePathDirty(value === 'duplicate' ? false : duplicatePathDirty)
    if (value === 'duplicate' && preview) {
      const targetName = duplicateName || (preview.name ? `${preview.name} (Copy)` : 'Library Copy')
      setDuplicatePath(derivePathFromName(preview.path, targetName))
    }
  }

  return (
    <div className="w-full flex flex-col bg-white">
      <div className="pt-8">
        <Stepper currentStep={4} steps={steps} />
      </div>

      <div className="px-6 py-6 pb-24">
        <div className="w-full max-w-6xl mx-auto">
          <h1 className="text-3xl font-bold mb-8">
            {isEditMode ? 'Edit library - Review' : 'Library Creation - Step 3: Review & Create'}
          </h1>

          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
              {error}
            </div>
          )}

          {loading ? (
            <div className="text-gray-500">Loading preview...</div>
          ) : (
            <div className="bg-white rounded-2xl border border-gray-200 shadow-sm">
              <div className="px-8 py-6 border-b border-gray-200">
                <h2 className="text-xl font-semibold">Review Configuration</h2>
              </div>

              <div className="px-8 py-6">
                <h3 className="text-base font-semibold mb-6">Configuration Summary</h3>
                
                <div className="grid grid-cols-2 gap-x-16 gap-y-6">
                  <div>
                    <div className="mb-4">
                      <div className="text-sm text-gray-600 mb-1">Name:</div>
                      <div className="text-base font-medium">{preview?.name || 'N/A'}</div>
                    </div>
                    <div className="mb-4">
                      <div className="text-sm text-gray-600 mb-1">Location:</div>
                      <div className="text-base font-medium">{preview?.path || 'Default location'}</div>
                    </div>
                    <div>
                      <div className="text-sm text-gray-600 mb-1">Description:</div>
                      <div className="text-base font-medium">
                        {preview?.description || 'No description provided'}
                      </div>
                    </div>
                  </div>

                  <div>
                    <div className="mb-4">
                      <div className="text-sm text-gray-600 mb-1">Papers:</div>
                      <div className="text-base font-medium">
                        {preview?.total_papers || 0} papers selected
                      </div>
                    </div>
                  </div>
                </div>
                {isEditMode && (
                  <div className="mt-8 space-y-5">
                    <div>
                      <Label className="text-sm font-medium text-gray-700 mb-2 block">
                        How should we save your changes?
                      </Label>
                      <div className="grid gap-4 md:grid-cols-2">
                        <EditModeCard
                          title="Update existing library"
                          description="Add or remove papers directly in this library."
                          value="update"
                          current={editMode}
                          onSelect={handleEditModeChange}
                        />
                        <EditModeCard
                          title="Save as a new library"
                          description="Create a copy at a new path while keeping the original intact."
                          value="duplicate"
                          current={editMode}
                          onSelect={handleEditModeChange}
                        />
                      </div>
                    </div>
                    {editMode === 'duplicate' && (
                      <div className="space-y-4 rounded-2xl border border-gray-200 bg-gray-50 p-5">
                        <div>
                          <Label htmlFor="duplicate-name" className="text-base font-semibold mb-2 block">
                            Library Name
                          </Label>
                          <Input
                            id="duplicate-name"
                            type="text"
                            value={duplicateName}
                            onChange={(e) => setDuplicateName(e.target.value)}
                            placeholder="My Research Library (Copy)"
                            className="w-full px-4 py-3 border-2 border-gray-300 rounded-xl shadow-md hover:shadow-lg focus:outline-none focus:ring-0 focus:border-blue-500 transition-all duration-200"
                          />
                        </div>
                        <div>
                          <Label htmlFor="duplicate-path" className="text-base font-semibold mb-2 block">
                            Location
                          </Label>
                          <Input
                            id="duplicate-path"
                            type="text"
                            value={duplicatePath}
                            onChange={(e) => {
                              setDuplicatePath(e.target.value)
                              setDuplicatePathDirty(true)
                            }}
                            placeholder={duplicatePathPlaceholder}
                            className="w-full px-4 py-3 border-2 border-gray-300 rounded-xl shadow-md hover:shadow-lg focus:outline-none focus:ring-0 focus:border-blue-500 transition-all duration-200 placeholder:text-gray-400"
                          />
                          <p className="text-xs text-gray-500 mt-2">
                            Adjust only if you want to save the duplicated library somewhere else.
                          </p>
                          {!duplicatePathValid && (
                            <p className="text-xs text-red-600 mt-1">Enter an absolute path (e.g., /data/library or C:\Libraries\MyCopy).</p>
                          )}
                        </div>
                        <div>
                          <Label htmlFor="duplicate-description" className="text-base font-semibold mb-2 block">
                            Description <span className="text-gray-500 font-normal">(Optional)</span>
                          </Label>
                          <textarea
                            id="duplicate-description"
                            value={duplicateDescription}
                            onChange={(e) => setDuplicateDescription(e.target.value)}
                            className="w-full min-h-[120px] px-4 py-3 border-2 border-gray-300 rounded-xl shadow-md hover:shadow-lg focus:outline-none focus:ring-0 focus:border-blue-500 resize-none transition-all duration-200"
                            placeholder="Add a short description for the duplicated library."
                          />
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="border-t border-gray-200 px-6 py-4 bg-white">
        <div className="max-w-6xl mx-auto flex justify-between">
          <Button
            variant="outline"
            className="px-6 py-2 rounded-full border-gray-300 shadow-md hover:shadow-lg transition-all duration-200"
            onClick={() => navigate(isEditMode ? '/create/staging/matched' : '/create/details')}
            disabled={creating}
          >
            Back
          </Button>
          <Button
            className="px-6 py-2 rounded-full bg-gray-900 text-white hover:bg-gray-800 shadow-md hover:shadow-lg transition-all duration-200 disabled:opacity-50"
            onClick={handlePrimaryAction}
            disabled={
              creating ||
              loading ||
              (isEditMode && editMode === 'duplicate' && (!duplicatePath.trim() || !duplicatePathValid))
            }
          >
            {creating ? 'Saving...' : primaryLabel}
          </Button>
        </div>
      </div>
    </div>
  )
}

function EditModeCard({ title, description, value, current, onSelect }) {
  const active = current === value
  return (
    <button
      type="button"
      onClick={() => onSelect(value)}
      className={`text-left rounded-2xl border p-4 transition ${
        active ? 'border-gray-900 bg-gray-900 text-white' : 'border-gray-200 bg-white text-gray-800'
      }`}
    >
      <p className="text-base font-semibold mb-1">{title}</p>
      <p className={`text-sm ${active ? 'text-gray-100' : 'text-gray-500'}`}>{description}</p>
    </button>
  )
}

function slugifyName(value) {
  return value
    ? value
        .toLowerCase()
        .trim()
        .replace(/[^a-z0-9]+/g, '-')
        .replace(/^-+|-+$/g, '')
    : ''
}

function parsePathInfo(path) {
  const trimmed = (path || '').trim()
  if (!trimmed) {
    return { type: 'posix', absolute: true, segments: [] }
  }
  const windowsMatch = trimmed.match(/^([a-zA-Z]:)([\\/].*)?$/)
  if (windowsMatch) {
    const drive = windowsMatch[1]
    const rest = (windowsMatch[2] || '').replace(/\\/g, '/')
    const segments = rest.split('/').filter(Boolean)
    return { type: 'windows', drive, segments }
  }
  const normalized = trimmed.replace(/\\/g, '/')
  const absolute = normalized.startsWith('/')
  const segments = normalized.split('/').filter(Boolean)
  return { type: 'posix', absolute, segments }
}

function derivePathFromName(currentPath, name) {
  const slug = slugifyName(name) || 'library-copy'
  const info = parsePathInfo(currentPath)
  if (info.type === 'windows') {
    const parentSegments = info.segments.slice(0, -1)
    const parent = parentSegments.length ? parentSegments.join('\\') + '\\' : ''
    return `${info.drive}\\${parent}${slug}`
  }
  const parentSegments = info.segments.slice(0, -1)
  const parent = parentSegments.join('/')
  const prefix = info.absolute ? '/' : ''
  if (parent) return `${prefix}${parent}/${slug}`
  return `${prefix}${slug}`
}
