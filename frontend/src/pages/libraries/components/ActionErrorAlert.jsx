import { AlertCircle } from 'lucide-react'

export default function ActionErrorAlert({ message }) {
  if (!message) return null
  return (
    <div className="rounded-2xl border border-red-200 bg-red-50 p-5 text-sm text-red-700 flex items-start gap-3">
      <AlertCircle className="w-5 h-5 mt-0.5 flex-shrink-0" />
      <div>
        <p className="font-semibold mb-1">Unable to attach library</p>
        <p>{message}</p>
      </div>
    </div>
  )
}
