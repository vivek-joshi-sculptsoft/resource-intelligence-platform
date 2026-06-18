import { useState, useRef, useEffect, useMemo } from 'react'
import { ChevronDown, Search, X } from 'lucide-react'

export interface SelectOption {
  value: string
  label: string
}

interface SearchableSelectProps {
  value: string
  onChange: (value: string) => void
  options: SelectOption[]
  placeholder?: string
  disabled?: boolean
  className?: string
  style?: React.CSSProperties
  variant?: 'form' | 'filter'
  error?: boolean
}

export function SearchableSelect({
  value,
  onChange,
  options,
  placeholder = 'Select...',
  disabled = false,
  className = '',
  style,
  variant = 'form',
  error = false,
}: SearchableSelectProps) {
  const [open, setOpen] = useState(false)
  const [query, setQuery] = useState('')
  const containerRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const listRef = useRef<HTMLDivElement>(null)
  const [highlightIndex, setHighlightIndex] = useState(0)

  const filtered = useMemo(() => {
    if (!query) return options
    const q = query.toLowerCase()
    return options.filter((o) => o.label.toLowerCase().includes(q))
  }, [options, query])

  useEffect(() => {
    setHighlightIndex(0)
  }, [filtered.length, query])

  useEffect(() => {
    if (!open) return
    function handleClickOutside(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false)
        setQuery('')
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [open])

  useEffect(() => {
    if (open && inputRef.current) {
      inputRef.current.focus()
    }
  }, [open])

  useEffect(() => {
    if (!open || !listRef.current) return
    const highlighted = listRef.current.children[highlightIndex] as HTMLElement | undefined
    if (highlighted) {
      highlighted.scrollIntoView?.({ block: 'nearest' })
    }
  }, [highlightIndex, open])

  const selectedLabel = options.find((o) => o.value === value)?.label

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === 'ArrowDown') {
      e.preventDefault()
      setHighlightIndex((i) => Math.min(i + 1, filtered.length - 1))
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      setHighlightIndex((i) => Math.max(i - 1, 0))
    } else if (e.key === 'Enter') {
      e.preventDefault()
      if (filtered[highlightIndex]) {
        onChange(filtered[highlightIndex].value)
        setOpen(false)
        setQuery('')
      }
    } else if (e.key === 'Escape') {
      setOpen(false)
      setQuery('')
    }
  }

  const isFilter = variant === 'filter'

  const borderColor = error ? '#ef4444' : '#D6DAF0'
  const focusBorderColor = error ? '#ef4444' : '#4A5BB5'

  const triggerBaseStyle: React.CSSProperties = {
    border: `1px solid ${open ? focusBorderColor : borderColor}`,
    color: disabled ? '#7C85C0' : '#1e1b4b',
    background: disabled ? '#F5F6FC' : isFilter ? '#F0F1FA' : '#fff',
    boxShadow: open ? '0 0 0 3px rgba(43,57,144,0.1)' : 'none',
    ...style,
  }

  return (
    <div ref={containerRef} className={`relative ${className}`}>
      <button
        type="button"
        disabled={disabled}
        onClick={() => { if (!disabled) setOpen(!open) }}
        className={`flex w-full items-center justify-between rounded-lg text-left outline-none transition-all ${
          isFilter
            ? 'py-[9px] pl-3.5 pr-8 text-[13.5px]'
            : 'px-3.5 py-[9px] text-[13.5px]'
        } ${disabled ? 'cursor-not-allowed opacity-60' : 'cursor-pointer'}`}
        style={triggerBaseStyle}
      >
        <span className={selectedLabel ? '' : 'opacity-50'}>
          {selectedLabel || placeholder}
        </span>
        <ChevronDown
          size={14}
          className={`shrink-0 transition-transform ${open ? 'rotate-180' : ''}`}
          style={{ color: '#7C85C0' }}
        />
      </button>

      {open && (
        <div
          className="absolute z-50 mt-1 w-full overflow-hidden rounded-lg shadow-lg"
          style={{ border: '1px solid #D6DAF0', background: '#fff' }}
        >
          <div
            className="flex items-center gap-2 px-3 py-2"
            style={{ borderBottom: '1px solid #ECEDF8' }}
          >
            <Search size={14} style={{ color: '#7C85C0', flexShrink: 0 }} />
            <input
              ref={inputRef}
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Type to search..."
              className="w-full bg-transparent text-[13px] outline-none"
              style={{ color: '#1e1b4b' }}
            />
            {query && (
              <button
                type="button"
                onClick={() => setQuery('')}
                className="shrink-0 cursor-pointer"
              >
                <X size={12} style={{ color: '#7C85C0' }} />
              </button>
            )}
          </div>

          <div ref={listRef} className="max-h-[200px] overflow-y-auto py-1">
            {filtered.length === 0 ? (
              <div className="px-3 py-2 text-[12.5px]" style={{ color: '#9ca3af' }}>
                No results found
              </div>
            ) : (
              filtered.map((opt, idx) => (
                <div
                  key={opt.value}
                  onClick={() => {
                    onChange(opt.value)
                    setOpen(false)
                    setQuery('')
                  }}
                  onMouseEnter={() => setHighlightIndex(idx)}
                  className="cursor-pointer px-3 py-2 text-[13px] transition-colors"
                  style={{
                    background: idx === highlightIndex ? '#F0F1FA' : value === opt.value ? '#F8F8FD' : 'transparent',
                    color: value === opt.value ? '#2B3990' : '#1e1b4b',
                    fontWeight: value === opt.value ? 600 : 400,
                  }}
                >
                  {opt.label}
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  )
}
