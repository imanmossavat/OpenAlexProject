import { useEffect, useMemo, useRef, useState } from 'react'
import clsx from 'clsx'
import { Markmap } from 'markmap-view'
import { Transformer } from 'markmap-lib'
import '@/styles/markmap.css'

const transformer = new Transformer()

export default function MarkmapRenderer({ markdown, annotations, className, height = 420 }) {
  const svgRef = useRef(null)
  const markmapRef = useRef(null)
  const [isLoaded, setIsLoaded] = useState(false)

  const prepared = useMemo(() => {
    const source = markdown || '# Workflow'
    console.log('Markdown source:', source)
    const { root } = transformer.transform(source)
    console.log('Transformed root:', root)
    applyAnnotations(root, annotations)
    return root
  }, [markdown, annotations])

  useEffect(() => {
    if (!svgRef.current || !prepared) {
      console.log('Missing ref or prepared data', { hasSvg: !!svgRef.current, hasPrepared: !!prepared })
      return
    }

    // Ensure SVG has explicit dimensions
    const svg = svgRef.current
    const rect = svg.getBoundingClientRect()
    console.log('SVG dimensions:', { width: rect.width, height: rect.height })

    if (!markmapRef.current) {
      console.log('Creating new Markmap instance with data:', prepared)
      
      try {
        markmapRef.current = Markmap.create(
          svg,
          {
            autoFit: true,
            color: (node) => {
              if (node.payload?.highlight) return '#7c3aed'
              return '#94a3b8' // Default color for links
            },
            paddingX: 8,
            spacingVertical: 5,
            spacingHorizontal: 80,
            initialExpandLevel: -1,
            pan: true,
            zoom: true,
            duration: 500,
            colorFreezeLevel: 0,
          },
          prepared,
        )
        
        console.log('Markmap created successfully:', markmapRef.current)
        
        // Function to apply stroke colors
        const applyStrokes = () => {
          const links = svg.querySelectorAll('.markmap-link')
          const lines = svg.querySelectorAll('.markmap-node line')
          const circles = svg.querySelectorAll('.markmap-node circle')
          
          console.log(`Applying strokes to ${links.length} links, ${lines.length} lines, ${circles.length} circles`)
          
          links.forEach(path => {
            path.style.stroke = '#94a3b8'
            path.style.strokeWidth = '2px'
          })
          lines.forEach(line => {
            line.style.stroke = '#7c3aed'
            line.style.strokeWidth = '1.5px'
          })
          circles.forEach(circle => {
            circle.style.stroke = '#7c3aed'
            circle.style.fill = '#ffffff'
            circle.style.strokeWidth = '2px'
          })
        }
        
        // Apply immediately
        applyStrokes()
        
        // Apply again after delays (in case Markmap re-renders)
        setTimeout(applyStrokes, 10)
        setTimeout(applyStrokes, 100)
        setTimeout(applyStrokes, 500)
        
        // Set loaded state to hide loading indicator
        setIsLoaded(true)
        
        // Give it a moment to render, then fit
        setTimeout(() => {
          if (markmapRef.current) {
            markmapRef.current.fit()
          }
        }, 100)
      } catch (error) {
        console.error('Error creating Markmap:', error)
      }
      
      return
    }

    console.log('Updating Markmap data')
    markmapRef.current.setData(prepared)
    markmapRef.current.fit()
  }, [prepared])

  useEffect(() => {
    return () => {
      markmapRef.current?.destroy?.()
      markmapRef.current = null
      setIsLoaded(false)
    }
  }, [])

  return (
    <div className={clsx('relative w-full overflow-hidden rounded-3xl border border-gray-200 bg-white shadow-sm', className)}>
      <svg 
        ref={svgRef} 
        className="markmap w-full" 
        style={{ height: `${height}px`, display: 'block', background: '#ffffff' }} 
      />
      {!isLoaded && (
        <div className="absolute inset-0 flex items-center justify-center text-gray-400">
          Loading workflow map...
        </div>
      )}
    </div>
  )
}

function applyAnnotations(root, annotations) {
  if (!root || !annotations?.stepStates?.length) return
  const children = root.children || []
  
  children.forEach((node, index) => {
    const state = annotations.stepStates[index]
    if (!state) return
    
    if (state.highlight) {
      node.payload = { ...(node.payload || {}), highlight: true }
    }
    
    // Set the node's state to collapsed if needed
    if (state.collapsed) {
      node.payload = { ...(node.payload || {}), fold: 1 }
    } else {
      node.payload = { ...(node.payload || {}), fold: 0 }
    }
  })
}