import { useDocumentTitle } from '../../shared/hooks/useDocumentTitle'

export function DashboardPage() {
  useDocumentTitle('Dashboard')

  return (
    <div>
      <h1 className="text-[22px] font-bold" style={{ color: '#1e1b4b' }}>Dashboard</h1>
      <p className="mt-2 text-[13px]" style={{ color: '#6b7280' }}>Dashboard content — built in S5-04</p>
    </div>
  )
}
