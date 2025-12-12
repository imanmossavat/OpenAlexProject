import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

export default function CustomPathPanel({
  manualPath,
  onChange,
  manualError,
  onSubmit,
  isValidPath,
}) {
  return (
    <div className="rounded-2xl border border-gray-200 p-6 bg-white shadow-sm">
      <h2 className="text-xl font-semibold text-gray-900 mb-4">Use a custom library path</h2>
      <div className="space-y-4">
        <div>
          <Label htmlFor="custom-path" className="text-sm text-gray-700">
            Library folder (absolute path)
          </Label>
          <Input
            id="custom-path"
            type="text"
            placeholder="/Users/me/Projects/ResearchLibrary"
            value={manualPath}
            onChange={(event) => onChange(event.target.value)}
            className="mt-1 font-mono rounded-full placeholder:text-gray-400"
          />
          <p className="text-xs text-gray-500 mt-2">
            We will validate the folder after you choose a workflow.
          </p>
        </div>
        {manualError ? <p className="text-sm text-red-600">{manualError}</p> : null}
        <Button className="w-full rounded-full" onClick={onSubmit} disabled={!isValidPath}>
          Use this path
        </Button>
      </div>
    </div>
  )
}
