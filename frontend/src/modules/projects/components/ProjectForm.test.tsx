import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router'
import { ProjectForm } from './ProjectForm'
import { useAuthStore } from '../../auth/store'

vi.mock('react-router', async () => {
  const actual = await vi.importActual('react-router')
  return { ...actual, useParams: () => ({}) }
})

vi.mock('../api', () => ({
  createProject: vi.fn().mockResolvedValue({ data: { id: 'new-1' } }),
  updateProject: vi.fn().mockResolvedValue({ data: { id: 'new-1' } }),
  fetchProject: vi.fn().mockResolvedValue({ data: null }),
}))

vi.mock('../../clients/api', () => ({
  fetchClients: vi.fn().mockResolvedValue({
    data: [{ id: 'c1', name: 'Acme Corp', industry: null, engagement_start_date: null, active_project_count: 0, is_active: true }],
    meta: { page: 1, limit: 100, total: 1, total_pages: 1 },
  }),
}))

vi.mock('../../resources/api', () => ({
  fetchResourcesDropdown: vi.fn().mockResolvedValue([
    { id: 'r1', name: 'Rajesh Kumar', employee_id: 'EMP001' },
    { id: 'r2', name: 'Priya Singh', employee_id: 'EMP002' },
  ]),
}))

function setRole(code: string, resourceId: string | null = null) {
  useAuthStore.setState({
    user: {
      id: 'u1',
      name: 'Test User',
      email: 'test@test.com',
      role: { id: 'r1', code, name: code, permission_level: 100 },
      resource_id: resourceId,
    },
    isAuthenticated: true,
    isLoading: false,
  })
}

function renderWithProviders() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <ProjectForm />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('ProjectForm', () => {
  beforeEach(() => {
    setRole('CEO')
  })

  it('renders create form title', async () => {
    renderWithProviders()
    expect(screen.getByText('Create New Project')).toBeInTheDocument()
  })

  it('renders required field labels', () => {
    renderWithProviders()
    expect(screen.getByText(/Project Name/)).toBeInTheDocument()
    expect(screen.getByText(/Project Type/)).toBeInTheDocument()
    expect(screen.getByText(/Delivery Manager/)).toBeInTheDocument()
    const pmLabels = screen.getAllByText(/Project Manager/)
    expect(pmLabels.length).toBeGreaterThan(0)
  })

  it('renders type radio buttons', () => {
    renderWithProviders()
    expect(screen.getByText('Fixed Price')).toBeInTheDocument()
    expect(screen.getByText('Time & Material')).toBeInTheDocument()
    expect(screen.getByText('Client Onboarding')).toBeInTheDocument()
  })

  it('shows validation errors on empty submit', async () => {
    renderWithProviders()
    fireEvent.click(screen.getByText('Create Project'))
    expect(await screen.findByText('Project name is required')).toBeInTheDocument()
    expect(screen.getByText('Client is required')).toBeInTheDocument()
  })

  it('shows contract end date required for T&M', async () => {
    renderWithProviders()
    fireEvent.click(screen.getByText('Time & Material'))
    fireEvent.click(screen.getByText('Create Project'))
    expect(await screen.findByText(/Contract end date is required/)).toBeInTheDocument()
  })

  it('pre-fills DM for DM role', async () => {
    setRole('DM', 'r1')
    renderWithProviders()
    await screen.findByText('Create New Project')
    const buttons = document.querySelectorAll('button[disabled]')
    const disabledDropdown = Array.from(buttons).find((b) => b.textContent?.includes('Select'))
    expect(disabledDropdown).toBeTruthy()
  })
})
