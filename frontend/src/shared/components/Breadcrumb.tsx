import { Link } from 'react-router'
import { ChevronRight, Home } from 'lucide-react'

export interface BreadcrumbItem {
  label: string
  to?: string
}

interface BreadcrumbProps {
  items: BreadcrumbItem[]
}

export function Breadcrumb({ items }: BreadcrumbProps) {
  return (
    <nav className="mb-4 flex items-center gap-1.5 text-[13px]">
      <Link
        to="/dashboard"
        className="flex items-center gap-1 no-underline transition-colors"
        style={{ color: '#7C85C0' }}
        onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.color = '#2B3990' }}
        onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.color = '#7C85C0' }}
      >
        <Home size={14} />
        <span>Home</span>
      </Link>
      {items.map((item, i) => (
        <span key={i} className="flex items-center gap-1.5">
          <ChevronRight size={14} style={{ color: '#D6DAF0' }} />
          {item.to ? (
            <Link
              to={item.to}
              className="no-underline transition-colors"
              style={{ color: '#7C85C0' }}
              onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.color = '#2B3990' }}
              onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.color = '#7C85C0' }}
            >
              {item.label}
            </Link>
          ) : (
            <span style={{ color: '#1e1b4b' }} className="font-medium">
              {item.label}
            </span>
          )}
        </span>
      ))}
    </nav>
  )
}
