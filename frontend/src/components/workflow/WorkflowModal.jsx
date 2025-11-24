import { useEffect, useMemo, useState } from 'react'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import WorkflowExplorer from '@/components/workflow/WorkflowExplorer'
import { findStepById } from '@/shared/workflows'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'

export default function WorkflowModal({
  open,
  onOpenChange,
  availableWorkflows = [],
  contextWorkflow,
  contextStepId,
}) {
  const [selectedWorkflowId, setSelectedWorkflowId] = useState(null)

  useEffect(() => {
    if (!open) return
    setSelectedWorkflowId(contextWorkflow?.id || null)
  }, [open, contextWorkflow?.id])

  const activeWorkflow = useMemo(() => {
    if (!selectedWorkflowId) return null
    return availableWorkflows.find((flow) => flow.id === selectedWorkflowId) || null
  }, [availableWorkflows, selectedWorkflowId])

  const displayStepId = activeWorkflow && contextWorkflow && activeWorkflow.id === contextWorkflow.id ? contextStepId : null
  const step = useMemo(() => findStepById(activeWorkflow, displayStepId), [activeWorkflow, displayStepId])
  const modalTitle = activeWorkflow
    ? `${activeWorkflow.title}${step ? ` – ${step.title}` : ''}`
    : 'Workflow overview'

  const handleOpenPage = () => {
    if (!activeWorkflow) return
    const params = new URLSearchParams()
    params.set('workflow', activeWorkflow.id)
    if (displayStepId) params.set('step', displayStepId)
    window.open(`/workflow${params.size ? `?${params.toString()}` : ''}`, '_blank', 'noopener,noreferrer')
  }

  const selectDisabled = availableWorkflows.length <= 1

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-5xl max-h-[90vh] bg-white overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center justify-between gap-3">
            <span>{modalTitle}</span>
            <Button variant="outline" size="sm" onClick={handleOpenPage} className="rounded-full shadow-sm" disabled={!activeWorkflow}>
              Open in new tab
            </Button>
          </DialogTitle>
          <p className="text-sm text-gray-500">
            Choose a workflow to explore its steps. When you open this from inside a flow, we highlight your current step and keep adjacent nodes expanded.
          </p>
        </DialogHeader>

        {!activeWorkflow && availableWorkflows.length ? (
          <div className="space-y-4">
            <p className="text-xs uppercase tracking-[0.3em] text-gray-500">Available workflows</p>
            <div className="space-y-4">
              {availableWorkflows.map((flow) => (
                <div
                  key={flow.id}
                  className="rounded-3xl border border-gray-200 px-5 py-4 shadow-sm bg-gradient-to-br from-white to-slate-50 flex items-center justify-between gap-4"
                >
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900">{flow.title}</h3>
                    <p className="text-sm text-gray-500">{flow.description}</p>
                  </div>
                  <Button className="rounded-full" onClick={() => setSelectedWorkflowId(flow.id)}>
                    Open workflow
                  </Button>
                </div>
              ))}
            </div>
          </div>
        ) : null}

        {activeWorkflow ? (
          <>
            {availableWorkflows.length > 1 ? (
              <div className="mb-6 space-y-2">
                <div className="flex items-center justify-between">
                  <p className="text-xs uppercase tracking-[0.3em] text-gray-500">Workflow</p>
                  <button
                    type="button"
                    className="text-xs text-gray-500 underline"
                    onClick={() => setSelectedWorkflowId(null)}
                  >
                    Choose another workflow
                  </button>
                </div>
                <Select value={activeWorkflow.id} onValueChange={setSelectedWorkflowId} disabled={selectDisabled}>
                  <SelectTrigger className="w-full rounded-full border-gray-300">
                    <SelectValue placeholder="Select workflow" />
                  </SelectTrigger>
                  <SelectContent>
                    {availableWorkflows.map((flow) => (
                      <SelectItem key={flow.id} value={flow.id}>
                        {flow.title}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            ) : null}

            <WorkflowExplorer workflow={activeWorkflow} currentStepId={displayStepId} />
          </>
        ) : null}

      </DialogContent>
    </Dialog>
  )
}
