import { useState, useRef, useEffect } from 'react'
import { Info } from 'lucide-react'

export interface InfoTooltipContent {
  formula: string
  meaning: string
  purpose: string
}

interface InfoTooltipProps {
  content: InfoTooltipContent
}

// Hover opens on desktop; click toggles + pins open for touch/keyboard access — both dismiss on outside click/Escape.
export function InfoTooltip({ content }: InfoTooltipProps) {
  const [open, setOpen] = useState(false)
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!open) return
    function handleClickOutside(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false)
      }
    }
    function handleEscape(e: KeyboardEvent) {
      if (e.key === 'Escape') setOpen(false)
    }
    document.addEventListener('mousedown', handleClickOutside)
    document.addEventListener('keydown', handleEscape)
    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
      document.removeEventListener('keydown', handleEscape)
    }
  }, [open])

  return (
    <div
      ref={containerRef}
      className="relative inline-flex"
      onMouseEnter={() => setOpen(true)}
      onMouseLeave={() => setOpen(false)}
    >
      <button
        type="button"
        onClick={(e) => {
          e.stopPropagation()
          setOpen((o) => !o)
        }}
        className="cursor-pointer text-[#A6ACDA] hover:text-[#7C85C0] transition-colors"
        aria-label="More information"
      >
        <Info size={13} />
      </button>

      {open && (
        <div
          onClick={(e) => e.stopPropagation()}
          className="absolute z-50 top-full right-0 mt-2 w-80 rounded-lg p-3.5 text-left normal-case"
          style={{
            background: '#1e1b4b',
            boxShadow: '0 8px 20px rgba(30,27,75,0.25)',
          }}
        >
          <div className="mb-2">
            <div className="text-[10px] font-semibold uppercase tracking-wide text-[#A6ACDA] mb-0.5">Formula</div>
            <div className="text-[11.5px] font-mono text-[#E8EAF6] leading-snug break-words">{content.formula}</div>
          </div>
          <div className="mb-2">
            <div className="text-[10px] font-semibold uppercase tracking-wide text-[#A6ACDA] mb-0.5">What it means</div>
            <div className="text-[11.5px] text-[#E8EAF6] leading-snug">{content.meaning}</div>
          </div>
          <div>
            <div className="text-[10px] font-semibold uppercase tracking-wide text-[#A6ACDA] mb-0.5">Why it matters</div>
            <div className="text-[11.5px] text-[#E8EAF6] leading-snug">{content.purpose}</div>
          </div>
        </div>
      )}
    </div>
  )
}
