import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Loader2 } from 'lucide-react'

export default function UseCaseDialog({
  open,
  pendingLibrary,
  useCases,
  onSelect,
  onOpenChange,
  selecting,
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="bg-white border border-gray-100">
        <DialogHeader>
          <DialogTitle>Choose a workflow</DialogTitle>
          <DialogDescription>
            Next, decide which workflow you want to launch using{' '}
            <span className="font-semibold">{pendingLibrary?.name || 'this library'}</span>.
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-3">
          {useCases.map((useCase) => (
            <button
              key={useCase.id}
              type="button"
              className="w-full text-left rounded-3xl border border-gray-200 bg-white p-4 hover:border-gray-900 hover:bg-gray-50 hover:shadow-lg transition disabled:opacity-50"
              onClick={() => onSelect(useCase)}
              disabled={selecting}
            >
              <p className="text-base font-semibold text-gray-900">{useCase.title}</p>
              <p className="text-sm text-gray-600">{useCase.description}</p>
            </button>
          ))}
        </div>
        {selecting ? (
          <div className="flex items-center text-sm text-gray-500 mt-4">
            <Loader2 className="w-4 h-4 animate-spin mr-2" />
            Setting up your session…
          </div>
        ) : null}
      </DialogContent>
    </Dialog>
  )
}
