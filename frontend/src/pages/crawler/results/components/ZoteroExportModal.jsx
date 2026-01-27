import { AlertCircle, Loader2, RefreshCcw } from 'lucide-react'

import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

export default function ZoteroExportModal({
  open,
  onClose,
  collections = [],
  loadingCollections = false,
  collectionsError = null,
  onRetryCollections,
  onOpenSettings,
  selectedCollectionKey,
  onSelectCollection,
  newCollectionName,
  onNewCollectionNameChange,
  dedupeEnabled,
  onToggleDedupe,
  tagsText,
  onTagsTextChange,
  submitting = false,
  onConfirm,
}) {
  const trimmedName = (newCollectionName || '').trim()
  const canSubmit = Boolean(selectedCollectionKey || trimmedName)
  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-2xl bg-white rounded-3xl border-0 shadow-2xl p-0">
        <DialogHeader className="px-6 pt-6 pb-2">
          <DialogTitle>Export to Zotero</DialogTitle>
        </DialogHeader>
        <div className="px-6 pb-6 space-y-5">
          <p className="text-sm text-gray-600">
            Choose a Zotero collection or create a new one. Selected catalog papers will be exported using your
            configured Zotero credentials.
          </p>

          <div className="flex items-center justify-between">
            <h3 className="font-semibold text-gray-900">Collections</h3>
            <Button
              type="button"
              variant="ghost"
              className="rounded-full text-xs flex items-center gap-1"
              onClick={onRetryCollections}
              disabled={loadingCollections}
            >
              {loadingCollections ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <RefreshCcw className="w-3.5 h-3.5" />}
              Refresh
            </Button>
          </div>

          <div className="max-h-64 overflow-y-auto border border-gray-100 rounded-2xl divide-y">
            {loadingCollections ? (
              <div className="flex items-center justify-center py-6 text-sm text-gray-500 gap-2">
                <Loader2 className="w-4 h-4 animate-spin" />
                Loading collections…
              </div>
            ) : collections.length ? (
              collections.map((collection) => (
                <label key={collection.key} className="flex items-center gap-3 px-4 py-3 text-sm">
                  <input
                    type="radio"
                    name="zotero-collection"
                    className="rounded border-gray-300 text-gray-900 focus:ring-gray-900"
                    checked={selectedCollectionKey === collection.key}
                    onChange={() => onSelectCollection(collection.key)}
                  />
                  <div>
                    <div className="font-semibold text-gray-900">{collection.name}</div>
                    <div className="text-xs text-gray-500">Key: {collection.key}</div>
                  </div>
                </label>
              ))
            ) : (
              <div className="px-4 py-6 text-sm text-gray-500">No collections found.</div>
            )}
          </div>

          {collectionsError ? (
            <div className="rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-red-700 space-y-2">
              <div className="flex gap-2 items-start">
                <AlertCircle className="w-4 h-4 mt-0.5" />
                <span>{collectionsError}</span>
              </div>
              {onOpenSettings ? (
                <Button
                  type="button"
                  variant="outline"
                  className="rounded-full text-xs"
                  onClick={onOpenSettings}
                >
                  Update integrations settings
                </Button>
              ) : null}
            </div>
          ) : null}

          <div className="space-y-3">
            <Label className="text-xs uppercase tracking-[0.3em] text-gray-500">Create new collection</Label>
            <Input
              value={newCollectionName}
              onChange={(e) => onNewCollectionNameChange(e.target.value)}
              placeholder="Optional new collection name"
              className="rounded-2xl placeholder:text-gray-400 placeholder:opacity-80"
            />
            <p className="text-xs text-gray-500">
              Provide a name to create a new collection. Leave blank to use one of the existing collections above.
            </p>
          </div>

          <label className="flex items-center gap-3 text-sm text-gray-700">
            <input
              type="checkbox"
              className="rounded border-gray-300 text-gray-900 focus:ring-gray-900"
              checked={dedupeEnabled}
              onChange={(e) => onToggleDedupe(e.target.checked)}
            />
            <span>Skip papers that already exist in Zotero (match by DOI or URL)</span>
          </label>

          <div className="space-y-3">
            <Label className="text-xs uppercase tracking-[0.3em] text-gray-500">Tags (optional)</Label>
            <Input
              value={tagsText}
              onChange={(e) => onTagsTextChange(e.target.value)}
              placeholder="Comma-separated tags"
              className="rounded-2xl placeholder:text-gray-400 placeholder:opacity-80"
            />
          </div>

          <div className="flex justify-end gap-3 pt-2">
            <Button variant="outline" className="rounded-full px-6" onClick={onClose} disabled={submitting}>
              Cancel
            </Button>
            <Button
              className="rounded-full px-6 bg-gray-900 text-white hover:bg-gray-800 disabled:opacity-60"
              onClick={onConfirm}
              disabled={!canSubmit || submitting}
            >
              {submitting ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin mr-2" />
                  Exporting…
                </>
              ) : (
                'Export selected'
              )}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}
