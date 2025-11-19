import { useEffect, useRef, useState } from 'react'
import { X, ExternalLink } from 'lucide-react'
import { Button } from '@/components/ui/button'

export default function PaperDetailModal({ paper, isOpen, onClose }) {
  const [shouldRender, setShouldRender] = useState(false)
  const [isAnimating, setIsAnimating] = useState(false)
  const [displayPaper, setDisplayPaper] = useState(null)
  const panelRef = useRef(null)
  const timeoutRef = useRef(null)

  useEffect(() => {
    if (isOpen && paper) {
      setDisplayPaper(paper)
    }
  }, [isOpen, paper])

  useEffect(() => {
    if (!isOpen) return
    const onKey = (e) => {
      if (e.key === 'Escape') onClose?.()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [isOpen, onClose])

  useEffect(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current)
      timeoutRef.current = null
    }

    if (isOpen) {
      setShouldRender(true)
      requestAnimationFrame(() => {
        requestAnimationFrame(() => {
          setIsAnimating(true)
        })
      })
    } else if (shouldRender) {
      setIsAnimating(false)
      
      timeoutRef.current = setTimeout(() => {
        setShouldRender(false)
        setDisplayPaper(null)
      }, 350)
    }

    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current)
        timeoutRef.current = null
      }
    }
  }, [isOpen, shouldRender])

  if (!shouldRender || !displayPaper) return null

  const authors = Array.isArray(displayPaper.authors)
    ? displayPaper.authors.join(', ')
    : (displayPaper.authors || '')
  const institutions = Array.isArray(displayPaper.institutions)
    ? displayPaper.institutions.join(', ')
    : (displayPaper.institutions || '')
  const venue = displayPaper.venue || ''
  const year = displayPaper.year || ''
  const citations = typeof displayPaper.cited_by_count === 'number' ? displayPaper.cited_by_count : null
  const references = typeof displayPaper.references_count === 'number' ? displayPaper.references_count : null
  const openAlexUrl = typeof displayPaper.paper_id === 'string' && /^[Ww]/.test(displayPaper.paper_id)
    ? `https://openalex.org/${displayPaper.paper_id}`
    : (displayPaper.url || null)

  return (
    <div
      className="fixed inset-0 z-50"
      onClick={onClose}
    >
      <div className={`absolute inset-0 bg-black/40 backdrop-blur-sm transition-opacity duration-300 ease-out ${isAnimating ? 'opacity-100' : 'opacity-0'}`} />

      <div
        ref={panelRef}
        className={`absolute inset-y-0 right-0 w-[60vw] bg-white shadow-2xl p-8 overflow-y-auto transform transition-transform duration-300 ease-out ${
          isAnimating ? 'translate-x-0' : 'translate-x-full'
        }`}
        onClick={(e) => e.stopPropagation()}
      >
        <button
          aria-label="Close"
          className="absolute top-4 right-4 p-1 rounded-full hover:bg-gray-100 transition-colors"
          onClick={onClose}
        >
          <X className="w-6 h-6" />
        </button>

        <h2 className="text-3xl font-bold mb-6 pr-12 break-words">{displayPaper.title || displayPaper.paper_id}</h2>

        {openAlexUrl && (
          <div className="mb-6">
            <Button
              variant="outline"
              className="bg-white border-gray-300"
              onClick={() => window.open(openAlexUrl, '_blank')}
            >
              OpenAlex <ExternalLink className="w-4 h-4 ml-2" />
            </Button>
          </div>
        )}

        {displayPaper.abstract && (
          <div className="mb-6">
            <div className="font-semibold text-sm text-gray-700 mb-2">Abstract:</div>
            <div className="text-sm text-gray-600 leading-relaxed whitespace-pre-wrap">{displayPaper.abstract}</div>
          </div>
        )}

        {authors && (
          <div className="mb-4">
            <div className="font-semibold text-sm text-gray-700">Authors:</div>
            <div className="text-sm text-gray-600">{authors}</div>
          </div>
        )}

        {venue && (
          <div className="mb-4">
            <div className="font-semibold text-sm text-gray-700">Source:</div>
            <div className="text-sm text-gray-600">{venue}</div>
          </div>
        )}

        {institutions && (
          <div className="mb-4">
            <div className="font-semibold text-sm text-gray-700">Institutions:</div>
            <div className="text-sm text-gray-600">{institutions}</div>
          </div>
        )}

        <div className="mb-4 space-y-1 text-sm text-gray-700">
          {typeof citations === 'number' && (
            <div><span className="font-semibold">Citations:</span> {citations}</div>
          )}
          {typeof references === 'number' && (
            <div><span className="font-semibold">References:</span> {references}</div>
          )}
          {year && (
            <div><span className="font-semibold">Year:</span> {year}</div>
          )}
        </div>
      </div>
    </div>
  )
}