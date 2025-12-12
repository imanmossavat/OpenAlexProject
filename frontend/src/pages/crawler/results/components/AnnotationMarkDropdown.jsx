import { Loader2 } from 'lucide-react'

import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'

export default function AnnotationMarkDropdown({ value, onChange, disabled, loading, marks }) {
  const resolvedValue = value || 'standard'
  return (
    <div className="relative w-full max-w-[150px]">
      <Select value={resolvedValue} onValueChange={onChange} disabled={disabled}>
        <SelectTrigger className="h-9 rounded-full border border-gray-200 px-3 pr-8 text-xs shadow-sm">
          <SelectValue />
        </SelectTrigger>
        <SelectContent className="rounded-2xl border border-gray-200 bg-white shadow-lg">
          {marks.map((mark) => (
            <SelectItem key={mark.value} value={mark.value}>
              {mark.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      {loading ? (
        <Loader2 className="absolute right-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 animate-spin text-gray-400" />
      ) : null}
    </div>
  )
}
