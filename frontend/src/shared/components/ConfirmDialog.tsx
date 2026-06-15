import { useEffect, useRef } from 'react'

interface ConfirmDialogProps {
  open: boolean
  title: string
  description: string
  confirmLabel?: string
  cancelLabel?: string
  variant?: 'danger' | 'default'
  onConfirm: () => void
  onCancel: () => void
}

export function ConfirmDialog({
  open,
  title,
  description,
  confirmLabel = 'Confirm',
  cancelLabel = 'Cancel',
  variant = 'default',
  onConfirm,
  onCancel,
}: ConfirmDialogProps) {
  const overlayRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!open) return
    function handleKey(e: KeyboardEvent) {
      if (e.key === 'Escape') onCancel()
    }
    document.addEventListener('keydown', handleKey)
    return () => document.removeEventListener('keydown', handleKey)
  }, [open, onCancel])

  if (!open) return null

  const confirmBg =
    variant === 'danger'
      ? 'linear-gradient(135deg, #ef4444, #dc2626)'
      : 'linear-gradient(135deg, #2B3990, #4A5BB5)'
  const confirmShadow =
    variant === 'danger'
      ? '0 2px 8px rgba(239,68,68,0.25)'
      : '0 2px 8px rgba(43,57,144,0.25)'

  return (
    <div
      ref={overlayRef}
      className="fixed inset-0 z-50 flex items-center justify-center"
      style={{ background: 'rgba(0,0,0,0.4)', backdropFilter: 'blur(2px)' }}
      onClick={(e) => { if (e.target === overlayRef.current) onCancel() }}
    >
      <div
        className="w-full max-w-[420px] rounded-xl p-6"
        style={{ background: '#fff', boxShadow: '0 20px 60px rgba(0,0,0,0.15)' }}
      >
        <h3 className="mb-2 text-[17px] font-bold" style={{ color: '#1e1b4b' }}>
          {title}
        </h3>
        <p className="mb-6 text-[14px] leading-relaxed" style={{ color: '#6b7280' }}>
          {description}
        </p>
        <div className="flex justify-end gap-3">
          <button
            onClick={onCancel}
            className="rounded-lg px-5 py-2.5 text-[14px] font-medium transition-colors"
            style={{ border: '1px solid #D6DAF0', background: '#fff', color: '#6b7280' }}
          >
            {cancelLabel}
          </button>
          <button
            onClick={onConfirm}
            className="rounded-lg border-none px-5 py-2.5 text-[14px] font-semibold text-white transition-all"
            style={{ background: confirmBg, boxShadow: confirmShadow }}
          >
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  )
}
