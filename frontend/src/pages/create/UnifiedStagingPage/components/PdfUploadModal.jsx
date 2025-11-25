import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'

export default function PdfUploadModal({
  open,
  onClose,
  files,
  setFiles,
  loading,
  error,
  onConfirm,
  onOpenGrobidGuide,
  grobidStatus,
}) {
  const onFileChange = (event) => {
    const list = Array.from(event.target.files || [])
    setFiles(list)
  }

  const grobidError =
    typeof error === 'string' &&
    error.toLowerCase().includes('grobid') &&
    error.toLowerCase().includes('service is not running')
  const grobidWarningMessage =
    grobidStatus?.checked && grobidStatus.available === false
      ? grobidStatus?.message ||
        'GROBID service is not running. Please start it before uploading PDF files.'
      : null
  const showGrobidGuideButton = Boolean((grobidWarningMessage || grobidError) && onOpenGrobidGuide)

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-2xl bg-white p-0 gap-0 rounded-3xl border-0 shadow-2xl">
        <DialogHeader className="px-6 pt-6 pb-2">
          <DialogTitle>Import from uploaded files</DialogTitle>
        </DialogHeader>
        <div className="px-6 pb-6 space-y-4">
          <div className="border-2 border-dashed border-gray-300 rounded-2xl p-6 text-center space-y-3">
            <p className="text-sm text-gray-600">Drop document files (PDF, DOCX, HTML, XML, LaTeX) here or browse</p>
            <div className="flex flex-col sm:flex-row gap-3 justify-center">
              <label className="inline-flex items-center gap-2 px-4 py-2 rounded-full border border-gray-300 cursor-pointer hover:bg-gray-50">
                <input
                  type="file"
                  multiple
                  accept=".pdf,.docx,.html,.htm,.xml,.tex"
                  onChange={onFileChange}
                  className="hidden"
                />
                <span className="text-sm font-medium text-gray-700">Browse files</span>
              </label>
              <label className="inline-flex items-center gap-2 px-4 py-2 rounded-full border border-gray-300 cursor-pointer hover:bg-gray-50">
                <input
                  type="file"
                  multiple
                  accept=".pdf,.docx,.html,.htm,.xml,.tex"
                  webkitdirectory=""
                  directory=""
                  onChange={onFileChange}
                  className="hidden"
                />
                <span className="text-sm font-medium text-gray-700">Select folder</span>
              </label>
            </div>
            <p className="text-xs text-gray-400">
              PDFs still require GROBID; other formats extract without it. Folder selection is available on Chromium-based browsers.
            </p>
          </div>
          {files.length > 0 && (
            <div className="max-h-48 overflow-y-auto border border-gray-100 rounded-2xl">
              {files.map((file) => (
                <div key={file.name} className="px-4 py-2 text-sm text-gray-700 border-b last:border-b-0">
                  {file.name} ({(file.size / (1024 * 1024)).toFixed(2)} MB)
                </div>
              ))}
            </div>
          )}
          {grobidWarningMessage && (
            <div className="text-sm text-red-600 space-y-2">
              <p>{grobidWarningMessage}</p>
              {showGrobidGuideButton && (
                <Button
                  type="button"
                  variant="ghost"
                  className="rounded-full px-4 text-xs text-red-600 hover:text-red-700 border border-red-100"
                  onClick={onOpenGrobidGuide}
                >
                  View GROBID setup guide
                </Button>
              )}
            </div>
          )}
          {error && (
            <div className="text-sm text-red-600 space-y-2">
              <p>{error}</p>
              {!grobidWarningMessage && grobidError && onOpenGrobidGuide && (
                <Button
                  type="button"
                  variant="ghost"
                  className="rounded-full px-4 text-xs text-red-600 hover:text-red-700 border border-red-100"
                  onClick={onOpenGrobidGuide}
                >
                  View GROBID setup guide
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
              disabled={loading || files.length === 0}
            >
              {loading ? 'Importing…' : 'Import PDFs'}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}
