type StatusType = 'ACTIVE' | 'INACTIVE' | 'COMPLETED' | 'ON_HOLD' | 'CANCELLED' | 'RELEASED' | 'AUTO_RELEASED'

const STATUS_STYLES: Record<StatusType, { bg: string; color: string; dot: string; label: string }> = {
  ACTIVE: { bg: 'rgba(34,197,94,0.1)', color: '#16a34a', dot: '#22c55e', label: 'Active' },
  INACTIVE: { bg: 'rgba(107,114,128,0.1)', color: '#6b7280', dot: '#9ca3af', label: 'Inactive' },
  COMPLETED: { bg: 'rgba(59,130,246,0.1)', color: '#2563eb', dot: '#3b82f6', label: 'Completed' },
  ON_HOLD: { bg: 'rgba(245,158,11,0.1)', color: '#d97706', dot: '#f59e0b', label: 'On Hold' },
  CANCELLED: { bg: 'rgba(239,68,68,0.1)', color: '#dc2626', dot: '#ef4444', label: 'Cancelled' },
  RELEASED: { bg: 'rgba(107,114,128,0.1)', color: '#6b7280', dot: '#9ca3af', label: 'Released' },
  AUTO_RELEASED: { bg: 'rgba(107,114,128,0.1)', color: '#6b7280', dot: '#9ca3af', label: 'Auto Released' },
}

interface StatusBadgeProps {
  status: string
  className?: string
}

export function StatusBadge({ status, className = '' }: StatusBadgeProps) {
  const style = STATUS_STYLES[status as StatusType] ?? STATUS_STYLES.INACTIVE

  return (
    <span
      className={`inline-flex items-center gap-[5px] rounded-full px-3 py-1 text-[12px] font-semibold ${className}`}
      style={{ background: style.bg, color: style.color }}
    >
      <span
        className="inline-block h-1.5 w-1.5 rounded-full"
        style={{ background: style.dot }}
      />
      {style.label}
    </span>
  )
}
