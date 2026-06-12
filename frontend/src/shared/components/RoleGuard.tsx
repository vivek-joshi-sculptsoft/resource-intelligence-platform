import { Navigate } from 'react-router'
import { useAuthStore } from '../../modules/auth/store'

interface RoleGuardProps {
  allowedRoles: string[]
  children: React.ReactNode
}

export function RoleGuard({ allowedRoles, children }: RoleGuardProps) {
  const { user } = useAuthStore()

  if (!user || !allowedRoles.includes(user.role.code)) {
    return <Navigate to="/" replace />
  }

  return <>{children}</>
}
