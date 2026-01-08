import { useMemo } from 'react'
import { useSearchParams } from 'react-router-dom'
import WorkflowExplorer from '@/components/workflow/WorkflowExplorer'
import { WORKFLOW_LIST, WORKFLOWS, findStepById } from '@/shared/workflows'

export default function WorkflowPage() {
  const [params] = useSearchParams()
  const requestedWorkflowId = params.get('workflow')
  const workflow = requestedWorkflowId ? WORKFLOWS[requestedWorkflowId] : null
  const activeWorkflow = workflow || WORKFLOW_LIST[0]
  const requestedStep = params.get('step')
  const currentStepId =
    activeWorkflow && requestedStep && activeWorkflow.steps.some((step) => step.id === requestedStep) ? requestedStep : null
  const step = useMemo(() => findStepById(activeWorkflow, currentStepId), [activeWorkflow, currentStepId])

  return (
    <div className="min-h-[calc(100vh-160px)] bg-white">
      <div className="max-w-5xl mx-auto px-6 py-12 space-y-6">
        <div>
          <p className="text-xs uppercase tracking-[0.4em] text-gray-500 mb-3">Create Workflow</p>
          <h1 className="text-4xl font-bold text-gray-900 mb-4">Workflow Overview</h1>
          <p className="text-gray-600 text-base">
            Explore the entire {activeWorkflow?.title?.toLowerCase() || 'workflow'}. Click on nodes inside the Markmap to collapse
            or expand sections.
            {step ? (
              <>
                {' '}
                This view focuses on <span className="font-semibold">{step.title}</span> because that is where you were when
                you opened it.
              </>
            ) : null}
          </p>
        </div>

        <WorkflowExplorer workflow={activeWorkflow} currentStepId={currentStepId} expandAll />
      </div>
    </div>
  )
}
