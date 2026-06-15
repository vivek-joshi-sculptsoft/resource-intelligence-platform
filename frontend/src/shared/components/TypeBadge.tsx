type ProjectType = 'FIXED_PRICE' | 'TIME_AND_MATERIAL' | 'CLIENT_ONBOARDING'

const TYPE_STYLES: Record<ProjectType, { bg: string; color: string; label: string }> = {
  FIXED_PRICE: { bg: '#E8EAF6', color: '#2B3990', label: 'FP' },
  TIME_AND_MATERIAL: { bg: '#FFF0EC', color: '#FF4B2B', label: 'T&M' },
  CLIENT_ONBOARDING: { bg: '#fef3c7', color: '#92400e', label: 'Onboarding' },
}

interface TypeBadgeProps {
  type: string
  className?: string
}

export function TypeBadge({ type, className = '' }: TypeBadgeProps) {
  const style = TYPE_STYLES[type as ProjectType] ?? { bg: '#f3f4f6', color: '#6b7280', label: type }

  return (
    <span
      className={`inline-block rounded-full px-2.5 py-[3px] text-[11px] font-semibold ${className}`}
      style={{ background: style.bg, color: style.color }}
    >
      {style.label}
    </span>
  )
}
