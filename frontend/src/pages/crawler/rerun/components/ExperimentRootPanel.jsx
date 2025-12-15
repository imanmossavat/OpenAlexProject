import { Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'

export default function ExperimentRootPanel({
  defaultRoot,
  rootInput,
  onChange,
  rootError,
  rootLoading,
  rootSaving,
  onSave,
  onReset,
  canSave,
}) {
  return (
    <div className="rounded-3xl border border-gray-200 bg-white shadow-sm p-5 space-y-4">
      <div>
        <p className="text-xs uppercase tracking-[0.3em] text-gray-400 mb-2">Experiments root</p>
        <h3 className="text-xl font-semibold text-gray-900">Default folder</h3>
        <p className="text-sm text-gray-600">
          We scan this path for crawler experiment folders. Update it if you keep experiments elsewhere.
        </p>
      </div>

      {rootLoading ? (
        <div className="flex items-center gap-2 text-sm text-gray-500">
          <Loader2 className="w-4 h-4 animate-spin" />
          Loading current root…
        </div>
      ) : (
        <>
          <Input
            value={rootInput}
            onChange={(e) => onChange(e.target.value)}
            placeholder={defaultRoot || 'Default ArticleCrawler path'}
            className="rounded-full placeholder:text-gray-400"
          />
          {rootError ? <p className="text-xs text-red-600">{rootError}</p> : null}
          <div className="flex flex-wrap gap-3">
            <Button className="rounded-full" onClick={onSave} disabled={!canSave || rootSaving}>
              {rootSaving ? 'Saving…' : 'Save default'}
            </Button>
            <Button
              variant="outline"
              className="rounded-full"
              onClick={onReset}
              disabled={rootSaving || !defaultRoot}
            >
              Reset to defaults
            </Button>
          </div>
        </>
      )}
    </div>
  )
}
