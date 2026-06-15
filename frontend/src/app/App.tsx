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
import { ResourcesPage } from './routes/resources/index'
import { ResourceProfilePage } from './routes/resources/profile'
import { ResourceFormPage } from './routes/resources/form'
import { ClientsPage } from './routes/clients/index'
import { ClientDetailPage } from './routes/clients/detail'
import { ClientFormPage } from './routes/clients/form'
import { ProjectsPage } from './routes/projects/index'
import { ProjectDetailPage } from './routes/projects/detail'
import { ProjectFormPage } from './routes/projects/form'
import { AvailabilityPage } from './routes/availability'
import { MyAssignmentsRoute } from './routes/my-assignments'

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
        {/* Resources */}
        <Route path="/resources" element={<ResourcesPage />} />
        <Route path="/resources/new" element={
          <RoleGuard allowedRoles={['CEO', 'CTO', 'HR']}><ResourceFormPage /></RoleGuard>
        } />
        <Route path="/resources/:id" element={<ResourceProfilePage />} />
        <Route path="/resources/:id/edit" element={
          <RoleGuard allowedRoles={['CEO', 'CTO', 'HR']}><ResourceFormPage /></RoleGuard>
        } />

        {/* Clients */}
        <Route path="/clients" element={<ClientsPage />} />
        <Route path="/clients/new" element={
          <RoleGuard allowedRoles={['CEO', 'CTO']}><ClientFormPage /></RoleGuard>
        } />
        <Route path="/clients/:id" element={<ClientDetailPage />} />
        <Route path="/clients/:id/edit" element={
          <RoleGuard allowedRoles={['CEO', 'CTO']}><ClientFormPage /></RoleGuard>
        } />

        {/* Availability */}
        <Route path="/availability" element={<AvailabilityPage />} />

        {/* My Assignments (Engineer worklog entry) */}
        <Route path="/my-assignments" element={<MyAssignmentsRoute />} />

        {/* Projects */}
        <Route path="/projects" element={<ProjectsPage />} />
        <Route path="/projects/:id" element={<ProjectDetailPage />} />
        <Route path="/projects/new" element={
          <RoleGuard allowedRoles={['CEO', 'CTO', 'DM']}><ProjectFormPage /></RoleGuard>
        } />
        <Route path="/projects/:id/edit" element={
          <RoleGuard allowedRoles={['CEO', 'CTO', 'DM', 'PM']}><ProjectFormPage /></RoleGuard>
        } />

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
