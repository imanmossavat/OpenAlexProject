import { useNavigate } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Workflow, HelpCircle, Settings as SettingsIcon } from 'lucide-react'
import fontysLogo from '@/assets/fontys.png'
import ixdLogo from '@/assets/ixd.svg'
import logo from '@/assets/logo.png'

export default function Header({ onOpenHelp }) {
  const navigate = useNavigate()
  const handleOpenHelp = () => {
    if (onOpenHelp) {
      onOpenHelp()
      return
    }
    navigate('/help')
  }
  return (
    <header className="w-full sticky top-0 bg-white border-b border-gray-200 z-40">
      <div className="w-full py-4 flex items-center justify-between px-4">
        <div className="flex items-center gap-8">
          <button type="button" onClick={() => navigate('/')} className="flex items-center gap-3 group">
            <img src={logo} alt="Crawler logo" className="h-12" />
            <span className="sr-only">Go to homepage</span>
          </button>
          <img src={fontysLogo} alt="Fontys" className="h-12" />
          <div className="flex items-center gap-3">
            <img src={ixdLogo} alt="IxD Logo" className="h-12" />
            <div className="font-semibold text-base">INTERACTION DESIGN</div>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="ghost" onClick={() => navigate('/about')} className="rounded-full">
            About us
          </Button>
          <Button variant="ghost" onClick={() => navigate('/settings/integrations')} className="rounded-full">
            <SettingsIcon className="w-4 h-4 mr-2" /> Settings
          </Button>
          <Button variant="outline" onClick={() => navigate('/workflow')} className="rounded-full">
            <Workflow className="w-4 h-4 mr-2" /> View workflow
          </Button>
          <Button className="rounded-full bg-purple-600 hover:bg-purple-700" onClick={handleOpenHelp}>
            <HelpCircle className="w-4 h-4 mr-2" /> Help & Guide
          </Button>
        </div>
      </div>
    </header>
  )
}
