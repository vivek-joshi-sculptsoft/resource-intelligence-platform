import { Navigate } from 'react-router'
import { useAuthStore } from '../../modules/auth/store'

interface RoleGuardProps {
  allowedRoles: string[]
  children: React.ReactNode
  /** When true, renders null instead of redirecting on unauthorized access */
  renderNull?: boolean
}

export function RoleGuard({ allowedRoles, children, renderNull = false }: RoleGuardProps) {
  const { user } = useAuthStore()

  if (!user || !allowedRoles.includes(user.role.code)) {
    return renderNull ? null : <Navigate to="/" replace />
  }

  return <>{children}</>
}
