import { Navigate } from 'react-router'
import { useAuthStore } from '../../modules/auth/store'
import { CompanyDashboard } from '../../modules/utilization/components/CompanyDashboard'
import { useDocumentTitle } from '../../shared/hooks/useDocumentTitle'

export function DashboardPage() {
  useDocumentTitle('Dashboard')
  const user = useAuthStore((s) => s.user)

  // See ACCESS-MATRIX.md — CEO/CTO see company dashboard, others redirect
  if (!user) return null
  if (!['CEO', 'CTO'].includes(user.role.code)) {
    return <Navigate to="/availability" replace />
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-[22px] font-bold" style={{ color: '#1e1b4b' }}>Company Dashboard</h1>
          <div className="text-[13px] mt-0.5" style={{ color: '#6b7280' }}>
            Real-time overview of resources, projects, and utilization
          </div>
        </div>
      </div>
      <CompanyDashboard />
    </div>
  )
}
