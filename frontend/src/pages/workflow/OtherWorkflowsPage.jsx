import { ArrowRight } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

import { Button } from '@/components/ui/button'

const EXTRA_WORKFLOWS = [
  {
    id: 'crawler-rerun',
    title: 'Re-run crawler experiment',
    description: 'Load a saved crawler configuration and run it again or adjust it in the wizard.',
    actionLabel: 'Browse experiments',
    path: '/crawler/reruns',
  },
]

export default function OtherWorkflowsPage() {
  const navigate = useNavigate()

  return (
    <div className="min-h-[calc(100vh-160px)] bg-white">
      <div className="max-w-5xl mx-auto px-6 py-16 space-y-8">
        <div className="space-y-3">
          <p className="text-xs uppercase tracking-[0.4em] text-gray-500">Other workflows</p>
          <h1 className="text-4xl font-bold text-gray-900">Explore additional actions</h1>
          <p className="text-lg text-gray-600">
            These workflows extend what you can do beyond the main library creation and editing flows.
          </p>
        </div>

        <div className="grid gap-6 md:grid-cols-2">
          {EXTRA_WORKFLOWS.map((workflow) => (
            <div
              key={workflow.id}
              className="rounded-3xl border border-gray-200 p-6 bg-gradient-to-b from-white to-gray-50 shadow-md hover:shadow-lg hover:-translate-y-[2px] active:translate-y-[1px] transition-all space-y-4"
            >
              <div>
                <p className="text-xs uppercase tracking-[0.3em] text-gray-400 mb-2">Workflow</p>
                <h2 className="text-2xl font-semibold text-gray-900">{workflow.title}</h2>
                <p className="text-gray-600 text-sm mt-2">{workflow.description}</p>
              </div>
              <Button
                className="rounded-full"
                onClick={() => {
                  navigate(workflow.path)
                }}
              >
                {workflow.actionLabel}
                <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
