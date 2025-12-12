import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Loader2 } from 'lucide-react'

export default function DefaultRootPanel({
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
    <div className="rounded-2xl border border-gray-200 p-6 bg-white shadow-sm">
      <h2 className="text-xl font-semibold text-gray-900 mb-4">Default discovery location</h2>
      {rootLoading ? (
        <div className="text-sm text-gray-500 flex items-center">
          <Loader2 className="w-4 h-4 animate-spin mr-2" />
          Loading current default…
        </div>
      ) : (
        <div className="space-y-4">
          <div className="text-sm text-gray-600">
            {defaultRoot ? (
              <>
                Currently scanning <span className="font-mono break-all inline-block">{defaultRoot}</span>{' '}
                before fallback directories.
              </>
            ) : (
              <>Using built-in discovery directories.</>
            )}
          </div>
          <div>
            <Label htmlFor="default-root" className="text-sm text-gray-700">
              Preferred library folder
            </Label>
            <Input
              id="default-root"
              type="text"
              placeholder="/absolute/path/to/libraries"
              value={rootInput}
              onChange={(event) => onChange(event.target.value)}
              className="mt-1 font-mono rounded-full"
            />
            <p className="text-xs text-gray-500 mt-2">This path is scanned first.</p>
          </div>
          {rootError ? <p className="text-sm text-red-600">{rootError}</p> : null}
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
        </div>
      )}
    </div>
  )
}
