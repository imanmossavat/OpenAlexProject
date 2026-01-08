import { useState } from 'react'
import { ChevronDown } from 'lucide-react'

export default function FilterSection({ title, children, defaultOpen = true }) {
  const [open, setOpen] = useState(defaultOpen)

  return (
    <div className="py-2 border-b border-gray-100 last:border-none">
      <button
        type="button"
        onClick={() => setOpen((prev) => !prev)}
        className="w-full flex items-center justify-between text-left text-sm font-semibold text-gray-800"
      >
        <span>{title}</span>
        <ChevronDown
          className={`w-4 h-4 transition-transform duration-200 ${open ? 'rotate-180' : ''}`}
        />
      </button>
      {open ? <div className="mt-3 space-y-3 text-sm text-gray-700">{children}</div> : null}
    </div>
  )
}
