import { useState, useRef, useEffect, useCallback } from 'react'
import { createPortal } from 'react-dom'
import { Info } from 'lucide-react'

export interface InfoTooltipContent {
  formula: string
  meaning: string
  purpose: string
}

interface InfoTooltipProps {
  content: InfoTooltipContent
}

export function InfoTooltip({ content }: InfoTooltipProps) {
  const [open, setOpen] = useState(false)
  const triggerRef = useRef<HTMLButtonElement>(null)
  const tooltipRef = useRef<HTMLDivElement>(null)
  const [pos, setPos] = useState({ top: 0, left: 0 })

  const updatePosition = useCallback(() => {
    if (!triggerRef.current) return
    const rect = triggerRef.current.getBoundingClientRect()
    const tooltipWidth = 320
    let left = rect.left + rect.width / 2 - tooltipWidth / 2
    if (left + tooltipWidth > window.innerWidth - 8) left = window.innerWidth - tooltipWidth - 8
    if (left < 8) left = 8
    setPos({ top: rect.bottom + 8, left })
  }, [])

  useEffect(() => {
    if (!open) return
    updatePosition()

    function handleClickOutside(e: MouseEvent) {
      if (
        triggerRef.current?.contains(e.target as Node) ||
        tooltipRef.current?.contains(e.target as Node)
      ) return
      setOpen(false)
    }
    function handleEscape(e: KeyboardEvent) {
      if (e.key === 'Escape') setOpen(false)
    }
    document.addEventListener('mousedown', handleClickOutside)
    document.addEventListener('keydown', handleEscape)
    window.addEventListener('scroll', updatePosition, true)
    window.addEventListener('resize', updatePosition)
    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
      document.removeEventListener('keydown', handleEscape)
      window.removeEventListener('scroll', updatePosition, true)
      window.removeEventListener('resize', updatePosition)
    }
  }, [open, updatePosition])

  return (
    <>
      <span
        className="relative inline-flex"
        onMouseEnter={() => setOpen(true)}
        onMouseLeave={(e) => {
          const related = e.relatedTarget as Node | null
          if (tooltipRef.current?.contains(related)) return
          setOpen(false)
        }}
      >
        <button
          ref={triggerRef}
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
      </span>

      {open && createPortal(
        <div
          ref={tooltipRef}
          onMouseEnter={() => setOpen(true)}
          onMouseLeave={() => setOpen(false)}
          onClick={(e) => e.stopPropagation()}
          className="fixed z-[9999] w-80 rounded-lg p-3.5 text-left normal-case"
          style={{
            top: pos.top,
            left: pos.left,
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
        </div>,
        document.body
      )}
    </>
  )
}
