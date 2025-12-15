import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

export default function CustomExperimentPathPanel({
  manualPath,
  onChange,
  manualError,
  onSubmit,
  isValidPath,
  disabled = false,
}) {
  return (
    <div className="rounded-2xl border border-gray-200 p-6 bg-white shadow-sm">
      <h2 className="text-xl font-semibold text-gray-900 mb-4">Use a custom experiment folder</h2>
      <div className="space-y-4">
        <div>
          <Label htmlFor="manual-experiment-path" className="text-sm text-gray-700">
            Experiment folder (absolute path)
          </Label>
          <Input
            id="manual-experiment-path"
            type="text"
            placeholder="D:\\OpenAlexProject\\experiments\\job_job_abc123"
            value={manualPath}
            onChange={(event) => onChange(event.target.value)}
            className="mt-1 font-mono rounded-full placeholder:text-gray-400"
            disabled={disabled}
          />
          <p className="text-xs text-gray-500 mt-2">
            Point directly to the experiment folder that contains <code>config.yaml</code>.
          </p>
        </div>
        {manualError ? <p className="text-sm text-red-600">{manualError}</p> : null}
        <Button className="w-full rounded-full" onClick={onSubmit} disabled={!isValidPath || disabled}>
          Use this experiment
        </Button>
      </div>
    </div>
  )
}
