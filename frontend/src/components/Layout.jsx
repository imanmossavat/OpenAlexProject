import { useMemo, useState } from 'react'
import { Outlet, useLocation } from 'react-router-dom'
import Header from '@/components/Header'
import HelpGuideModal from '@/components/help/HelpGuideModal'
import { getHelpContent } from '@/components/help/helpContent'
import WorkflowModal from '@/components/workflow/WorkflowModal'
import { WORKFLOW_LIST, getWorkflowContext } from '@/shared/workflows'
import { Toaster } from '@/components/ui/toaster'

export default function Layout() {
  const location = useLocation()
  const [isHelpOpen, setIsHelpOpen] = useState(false)
  const [isWorkflowOpen, setIsWorkflowOpen] = useState(false)

  const helpContent = useMemo(() => getHelpContent(location.pathname), [location.pathname])
  const workflowContext = useMemo(() => getWorkflowContext(location.pathname), [location.pathname])

  return (
    <div className="min-h-screen flex flex-col bg-white">
      <Header onOpenHelp={() => setIsHelpOpen(true)} onOpenWorkflow={() => setIsWorkflowOpen(true)} />
      <main className="flex-1">
        <Outlet />
      </main>
      <HelpGuideModal isOpen={isHelpOpen} onClose={() => setIsHelpOpen(false)} content={helpContent} />
      <WorkflowModal
        open={isWorkflowOpen}
        onOpenChange={setIsWorkflowOpen}
        availableWorkflows={WORKFLOW_LIST}
        contextWorkflow={workflowContext.workflow}
        contextStepId={workflowContext.stepId}
      />
      <Toaster />
    </div>
  )
}
