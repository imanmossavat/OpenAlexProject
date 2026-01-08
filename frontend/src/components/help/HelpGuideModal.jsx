import { useEffect } from 'react'
import { HelpCircle, X } from 'lucide-react'

export default function HelpGuideModal({ isOpen, onClose, content }) {
  useEffect(() => {
    if (!isOpen) return undefined
    const handleKey = (event) => {
      if (event.key === 'Escape') onClose?.()
    }
    window.addEventListener('keydown', handleKey)
    return () => window.removeEventListener('keydown', handleKey)
  }, [isOpen, onClose])

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center px-4 py-8">
      <div className="absolute inset-0 bg-black/40 backdrop-blur-[1px]" onClick={onClose} />
      <div className="relative w-full max-w-4xl bg-white rounded-3xl shadow-2xl border border-gray-100 overflow-hidden">
        <header className="flex items-start gap-3 px-8 py-6 border-b border-gray-100">
          <div className="flex items-center justify-center w-12 h-12 rounded-2xl bg-purple-100 text-purple-600">
            <HelpCircle className="w-6 h-6" />
          </div>
          <div className="flex-1">
            <p className="text-xs uppercase tracking-[0.3em] text-purple-500 font-semibold">{content.contextLabel}</p>
            <h2 className="text-2xl font-semibold text-gray-900">{content.title}</h2>
            <p className="text-sm text-gray-500 mt-2">{content.intro}</p>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close help modal"
            className="p-2 rounded-full border border-gray-200 hover:border-gray-300 hover:bg-gray-50 transition"
          >
            <X className="w-4 h-4 text-gray-600" />
          </button>
        </header>

        <div className="px-8 py-8">
          <div className="grid gap-5 md:grid-cols-2">
            {content.sections.map((section) => (
              <article
                key={section.title}
                className="bg-white rounded-2xl border border-gray-100 shadow-lg p-6 flex flex-col gap-4"
              >
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">{section.title}</h3>
                  <p className="text-sm text-gray-500">{section.description}</p>
                </div>
                <ul className="space-y-2 text-sm text-gray-600">
                  {section.bullets.map((bullet) => (
                    <li key={bullet} className="flex items-start gap-2">
                      <span className="mt-1 h-2 w-2 rounded-full bg-purple-500" />
                      <span>{bullet}</span>
                    </li>
                  ))}
                </ul>
              </article>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

