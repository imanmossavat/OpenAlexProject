import { useMemo, useState } from 'react'
import { HelpCircle } from 'lucide-react'

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'

const DEFAULT_EXAMPLES = [
  'Drop the list into NotebookLM or other notebooks to summarize papers or ask follow-up questions.',
  'Share the clean URLs with collaborators.',
  'Reuse the links as seeds for new crawler runs, API lookups, or citation checks.',
]

export default function CopyUsageHelp({
  contextLabel = 'these URLs',
  tooltip = 'Copy URL usage tips',
  examples,
  descriptionOverride,
  extraSections = [],
  hideDefaultExamples = false,
}) {
  const [open, setOpen] = useState(false)
  const resolvedExamples = useMemo(() => {
    if (hideDefaultExamples) return Array.isArray(examples) ? examples : []
    if (Array.isArray(examples) && examples.length) return examples
    return DEFAULT_EXAMPLES
  }, [examples, hideDefaultExamples])

  const baseDescription = `Copy ${contextLabel} to keep researching outside this tab.`
  const description = descriptionOverride || baseDescription

  return (
    <>
      <button
        type="button"
        title={tooltip}
        aria-label={tooltip}
        className="rounded-full border border-gray-200 bg-white w-8 h-8 flex items-center justify-center text-gray-500 hover:text-gray-900 hover:border-gray-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-gray-400 transition-colors"
        onClick={() => setOpen(true)}
      >
        <HelpCircle className="w-4 h-4" />
      </button>
      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent className="sm:max-w-md bg-white rounded-3xl border-0 shadow-2xl">
          <DialogHeader>
            <DialogTitle>Ways to use copied links</DialogTitle>
            <DialogDescription>{description}</DialogDescription>
          </DialogHeader>
          <div className="space-y-3 text-sm text-gray-600">
            {resolvedExamples.length ? (
              <ul className="list-disc pl-5 space-y-1">
                {resolvedExamples.map((example, index) => (
                  <li key={`${example}-${index}`}>{example}</li>
                ))}
              </ul>
            ) : null}
            {extraSections.map(({ title, content }, index) => (
              <div key={`${title}-${index}`} className="space-y-1">
                {title ? <p className="font-semibold text-gray-700">{title}</p> : null}
                <p className="text-sm text-gray-600">{content}</p>
              </div>
            ))}
            <p className="text-xs text-gray-400">
              Tip: the clipboard keeps your most recent list, so you can paste it anywhere (NotebookLM,
              docs, chats).
            </p>
          </div>
        </DialogContent>
      </Dialog>
    </>
  )
}
