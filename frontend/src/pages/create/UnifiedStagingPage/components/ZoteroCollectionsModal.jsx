import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'

export default function ZoteroCollectionsModal({
  open,
  onClose,
  collections,
  selected,
  setSelected,
  loading,
  error,
  onConfirm,
  onOpenSettings,
}) {
  const toggle = (key) => {
    setSelected((prev) => ({ ...prev, [key]: !prev[key] }))
  }
  const allSelected = collections.length > 0 && collections.every((c) => selected[c.key])

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-2xl bg-white p-0 gap-0 rounded-3xl border-0 shadow-2xl">
        <DialogHeader className="px-6 pt-6 pb-2">
          <DialogTitle>Import from Zotero</DialogTitle>
        </DialogHeader>
        <div className="px-6 pb-6 space-y-4">
          <div className="flex items-center justify-between text-sm">
            <Button
              variant="ghost"
              className="rounded-full px-4"
              onClick={() => {
                const next = {}
                collections.forEach((c) => {
                  next[c.key] = true
                })
                setSelected(next)
              }}
            >
              Select all
            </Button>
            <Button
              variant="ghost"
              className="rounded-full px-4"
              onClick={() => {
                const next = {}
                collections.forEach((c) => {
                  next[c.key] = false
                })
                setSelected(next)
              }}
            >
              Clear
            </Button>
          </div>
          <div className="max-h-80 overflow-y-auto border border-gray-100 rounded-2xl divide-y">
            {collections.map((collection) => (
              <label key={collection.key} className="flex items-center gap-3 px-4 py-3 text-sm">
                <input
                  type="checkbox"
                  className="rounded border-gray-300 text-gray-900 focus:ring-gray-900"
                  checked={!!selected[collection.key]}
                  onChange={() => toggle(collection.key)}
                />
                <div>
                  <div className="font-semibold text-gray-900">{collection.name}</div>
                  <div className="text-xs text-gray-500">Key: {collection.key}</div>
                </div>
              </label>
            ))}
            {!collections.length && (
              <div className="px-4 py-6 text-sm text-gray-500">No collections available.</div>
            )}
          </div>
          {error && (
            <div className="text-sm text-red-600 space-y-2">
              <p>{error}</p>
              {onOpenSettings && (
                <Button
                  type="button"
                  variant="ghost"
                  className="rounded-full px-4 text-xs text-red-600 hover:text-red-700 border border-red-100"
                  onClick={onOpenSettings}
                >
                  Update Zotero settings
                </Button>
              )}
            </div>
          )}
          <div className="flex justify-end gap-3">
            <Button variant="outline" className="rounded-full px-6" onClick={onClose} disabled={loading}>
              Cancel
            </Button>
            <Button
              className="rounded-full px-6 bg-gray-900 text-white hover:bg-gray-800 disabled:opacity-60"
              onClick={onConfirm}
              disabled={loading || collections.length === 0 || (!allSelected && !Object.values(selected).some(Boolean))}
            >
              {loading ? 'Importing…' : 'Import selected'}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}
