import { useMemo } from 'react'
import MarkmapRenderer from '@/components/workflow/MarkmapRenderer'
import { findStepById } from '@/shared/workflows'

export default function WorkflowExplorer({ workflow, currentStepId, expandAll = false, neighborRange = 1 }) {
  const markdown = useMemo(() => buildMarkdown(workflow, currentStepId), [workflow, currentStepId])
  const annotations = useMemo(
    () => buildAnnotations(workflow, currentStepId, expandAll, neighborRange),
    [workflow, currentStepId, expandAll, neighborRange],
  )

  if (!workflow) return null
  const currentStep = findStepById(workflow, currentStepId)

  return (
    <div className="space-y-4">
      {currentStep && (
        <div className="rounded-2xl border border-purple-100 bg-purple-50 px-4 py-3 text-sm text-purple-900">
          <p className="mb-2">
            Currently viewing <span className="font-semibold">{currentStep.title}</span>. The Markmap keeps the adjacent steps
            expanded so you never lose context—feel free to click nodes to explore the rest.
          </p>
          <p className="text-purple-700">
            This map stays in sync with where you are in the library creation flow. Click any node to drill down, or open
            the full-page view for more room.
          </p>
        </div>
      )}
      <MarkmapRenderer markdown={markdown} annotations={annotations} height={500} />
    </div>
  )
}

function buildMarkdown(workflow, currentStepId) {
  if (!workflow) return '# Workflow'
  
  const lines = [`# ${workflow.title}`]
  
  if (workflow.description) {
    lines.push('', workflow.description)
  }
  
  lines.push('')
  
  workflow.steps.forEach((step, index) => {
    const prefix = `${index + 1}. `
    const activeSuffix = step.id === currentStepId ? ' *(you are here)*' : ''
    lines.push(`## ${prefix}${step.title}${activeSuffix}`)
    
    if (step.summary) {
      lines.push('', step.summary)
    }
    
    if (step.details && step.details.length > 0) {
      lines.push('')
      step.details.forEach((detail) => {
        lines.push(`- **${detail.title}:** ${detail.description}`)
      })
    }
    
    lines.push('')
  })
  
  return lines.join('\n')
}

function buildAnnotations(workflow, currentStepId, expandAll, neighborRange) {
  const steps = workflow?.steps || []
  const currentIndex = steps.findIndex((step) => step.id === currentStepId)
  
  if (currentIndex === -1 || expandAll) {
    return {
      stepStates: steps.map((step) => ({ 
        collapsed: false, 
        highlight: step.id === currentStepId 
      })),
    }
  }
  
  return {
    stepStates: steps.map((step, index) => ({
      collapsed: Math.abs(index - currentIndex) > neighborRange,
      highlight: step.id === currentStepId,
    })),
  }
}