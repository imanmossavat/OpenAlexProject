import { Button } from '@/components/ui/button'
import { CheckCircle2 } from 'lucide-react'

export default function LatestSelectionAlert({ latestSelection, onContinue }) {
  if (!latestSelection) return null
  return (
    <div className="rounded-2xl border border-green-200 bg-green-50 p-6 flex items-start gap-4">
      <CheckCircle2 className="w-6 h-6 text-green-500 mt-0.5 flex-shrink-0" />
      <div>
        <p className="text-lg font-semibold text-green-900 mb-1">
          {latestSelection.libraryName} is ready for the {latestSelection.useCase.title.toLowerCase()}.
        </p>
        <p className="text-sm text-green-900 mb-2">
          Session <span className="font-mono">{latestSelection.sessionId}</span> now tracks this library at{' '}
          <span className="font-mono">{latestSelection.libraryPath}</span>.
        </p>
        {latestSelection.nextPath ? (
          <Button
            className="rounded-full bg-green-600 hover:bg-green-700"
            onClick={() => onContinue(latestSelection.nextPath)}
          >
            Continue to crawler
          </Button>
        ) : null}
      </div>
    </div>
  )
}
