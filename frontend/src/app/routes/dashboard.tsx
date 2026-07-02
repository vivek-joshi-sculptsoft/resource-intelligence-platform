import { Navigate } from 'react-router'
import { useAuthStore } from '../../modules/auth/store'
import { CompanyDashboard } from '../../modules/utilization/components/CompanyDashboard'
import { DMDashboard } from '../../modules/utilization/components/DMDashboard'
import { useDocumentTitle } from '../../shared/hooks/useDocumentTitle'

export function DashboardPage() {
  useDocumentTitle('Dashboard')
  const user = useAuthStore((s) => s.user)

  if (!user) return null

  // See ACCESS-MATRIX.md — CEO/CTO see company dashboard, DM sees portfolio dashboard
  if (user.role.code === 'DM') {
    return (
      <div>
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-[22px] font-bold" style={{ color: '#1e1b4b' }}>Portfolio Dashboard</h1>
            <div className="text-[13px] mt-0.5" style={{ color: '#6b7280' }}>
              Your delivery portfolio — projects, resources, and financials
            </div>
          </div>
        </div>
        <DMDashboard />
      </div>
    )
  }

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
