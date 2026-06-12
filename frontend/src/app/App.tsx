import { useEffect } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router'
import { Toaster } from 'sonner'
import { useAuthStore } from '../modules/auth/store'
import { ProtectedRoute } from '../shared/components/ProtectedRoute'
import { RoleGuard } from '../shared/components/RoleGuard'
import { RootLayout } from './routes/_layout'
import { LoginPage } from './routes/login'
import { DashboardPage } from './routes/dashboard'
import { UsersPage } from './routes/admin/users'
import { UserFormPage } from './routes/admin/user-form'
import { RolesPage } from './routes/admin/roles'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30 * 1000,
      retry: 1,
    },
  },
})

function AppRoutes() {
  const restoreSession = useAuthStore((s) => s.restoreSession)

  useEffect(() => {
    restoreSession()
  }, [restoreSession])

  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        element={
          <ProtectedRoute>
            <RootLayout />
          </ProtectedRoute>
        }
      >
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route
          path="/admin/users"
          element={
            <RoleGuard allowedRoles={['CEO', 'CTO']}>
              <UsersPage />
            </RoleGuard>
          }
        />
        <Route
          path="/admin/users/new"
          element={
            <RoleGuard allowedRoles={['CEO', 'CTO']}>
              <UserFormPage />
            </RoleGuard>
          }
        />
        <Route
          path="/admin/users/:id/edit"
          element={
            <RoleGuard allowedRoles={['CEO', 'CTO']}>
              <UserFormPage />
            </RoleGuard>
          }
        />
        <Route
          path="/admin/roles"
          element={
            <RoleGuard allowedRoles={['CEO', 'CTO']}>
              <RolesPage />
            </RoleGuard>
          }
        />
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
      </Route>
    </Routes>
  )
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AppRoutes />
      </BrowserRouter>
      <Toaster position="top-right" />
    </QueryClientProvider>
  )
}
