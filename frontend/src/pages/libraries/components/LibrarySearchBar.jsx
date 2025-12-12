import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

export default function LibrarySearchBar({ value, onChange, onClear, disabled }) {
  return (
    <div className="bg-white border border-gray-200 rounded-2xl p-4 flex flex-col md:flex-row md:items-center md:justify-between gap-3">
      <div className="flex-1">
        <Label htmlFor="search" className="text-xs uppercase tracking-wider text-gray-500">
          Search libraries
        </Label>
        <Input
          id="search"
          type="text"
          placeholder="Filter by name or description"
          value={value}
          onChange={(event) => onChange(event.target.value)}
          className="mt-1 rounded-full placeholder:text-gray-400"
        />
      </div>
      <div className="flex gap-2 md:mt-6">
        <Button
          type="button"
          variant="outline"
          className="rounded-full"
          onClick={onClear}
          disabled={disabled}
        >
          Clear
        </Button>
      </div>
    </div>
  )
}
