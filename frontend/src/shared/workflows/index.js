import { createWorkflow } from '@/shared/workflows/createWorkflow'
import { crawlerWorkflow } from '@/shared/workflows/crawlerWorkflow'

export const WORKFLOW_LIST = [createWorkflow, crawlerWorkflow]
export const DEFAULT_WORKFLOW = WORKFLOW_LIST[0]

const routeToWorkflow = (() => {
  const map = new Map()
  WORKFLOW_LIST.forEach((flow) => {
    flow.steps.forEach((step) => {
      ;(step.routes || []).forEach((route) => {
        map.set(route, { workflowId: flow.id, stepId: step.id })
      })
    })
  })
  return map
})()

export const WORKFLOWS = Object.fromEntries(WORKFLOW_LIST.map((flow) => [flow.id, flow]))

export function getWorkflowContext(pathname) {
  if (!pathname) return { workflow: null, stepId: null }
  const exact = routeToWorkflow.get(pathname)
  if (exact) {
    return {
      workflow: WORKFLOWS[exact.workflowId] || DEFAULT_WORKFLOW,
      stepId: exact.stepId,
    }
  }

  // Handle nested or parameterized paths by checking prefix
  const found = Array.from(routeToWorkflow.entries()).find(([route]) => pathname.startsWith(route))
  if (found) {
    const [, value] = found
    return {
      workflow: WORKFLOWS[value.workflowId] || DEFAULT_WORKFLOW,
      stepId: value.stepId,
    }
  }

  return { workflow: null, stepId: null }
}

export function findStepById(workflow, stepId) {
  if (!workflow || !stepId) return null
  return workflow.steps.find((step) => step.id === stepId) || null
}
