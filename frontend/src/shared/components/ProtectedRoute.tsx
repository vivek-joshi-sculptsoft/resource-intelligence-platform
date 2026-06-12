import { Navigate } from 'react-router'
import { useAuthStore } from '../../modules/auth/store'

export function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuthStore()

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="text-sm text-gray-500">Loading...</div>
      </div>
    )
  }

  if (!isAuthenticated) return <Navigate to="/login" replace />

  return <>{children}</>
}
