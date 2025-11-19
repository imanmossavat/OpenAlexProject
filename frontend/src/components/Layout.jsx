import { useMemo, useState } from 'react'
import { Outlet, useLocation } from 'react-router-dom'
import Header from '@/components/Header'
import HelpGuideModal from '@/components/help/HelpGuideModal'
import { getHelpContent } from '@/components/help/helpContent'

export default function Layout() {
  const location = useLocation()
  const [isHelpOpen, setIsHelpOpen] = useState(false)

  const helpContent = useMemo(() => getHelpContent(location.pathname), [location.pathname])

  return (
    <div className="min-h-screen flex flex-col bg-white">
      <Header onOpenHelp={() => setIsHelpOpen(true)} />
      <main className="flex-1">
        <Outlet />
      </main>
      <HelpGuideModal isOpen={isHelpOpen} onClose={() => setIsHelpOpen(false)} content={helpContent} />
    </div>
  )
}
