import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router'
import { ProjectList } from './ProjectList'
import { useAuthStore } from '../../auth/store'

vi.mock('../api', () => ({
  fetchProjects: vi.fn().mockResolvedValue({
    data: [
      {
        id: '1',
        name: 'Project Alpha',
        client_name: 'Acme Corp',
        type: 'FIXED_PRICE',
        status: 'ACTIVE',
        billing_currency: 'INR',
        dm_name: 'Rajesh',
        pm_name: 'Priya',
        start_date: '2026-01-01',
        contract_end_date: '2026-12-31',
      },
      {
        id: '2',
        name: 'Project Beta',
        client_name: 'Tech Ltd',
        type: 'TIME_AND_MATERIAL',
        status: 'ON_HOLD',
        billing_currency: 'USD',
        dm_name: 'Amit',
        pm_name: 'Sneha',
        start_date: '2026-03-01',
        contract_end_date: null,
      },
    ],
    meta: { page: 1, limit: 20, total: 2, total_pages: 1 },
  }),
}))

vi.mock('../../clients/api', () => ({
  fetchClients: vi.fn().mockResolvedValue({ data: [], meta: { page: 1, limit: 100, total: 0, total_pages: 0 } }),
}))

function setRole(code: string) {
  useAuthStore.setState({
    user: {
      id: 'u1',
      name: 'Test User',
      email: 'test@test.com',
      role: { id: 'r1', code, name: code, permission_level: 100 },
      resource_id: null,
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
        <ProjectList />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('ProjectList', () => {
  beforeEach(() => {
    setRole('CEO')
  })

  it('renders project rows', async () => {
    renderWithProviders()
    expect(await screen.findByText('Project Alpha')).toBeInTheDocument()
    expect(screen.getByText('Project Beta')).toBeInTheDocument()
    expect(screen.getByText('Acme Corp')).toBeInTheDocument()
  })

  it('shows Add Project button for CEO', async () => {
    renderWithProviders()
    expect(await screen.findByText('Add Project')).toBeInTheDocument()
  })

  it('hides Add Project button for ENGINEER', async () => {
    setRole('ENGINEER')
    renderWithProviders()
    await screen.findByText('Project Alpha')
    expect(screen.queryByText('Add Project')).not.toBeInTheDocument()
  })

  it('renders status filter dropdown', async () => {
    renderWithProviders()
    await screen.findByText('Project Alpha')
    const filterButtons = document.querySelectorAll('button[type="button"]')
    const statusButton = Array.from(filterButtons).find((b) => b.textContent?.includes('Active'))
    expect(statusButton).toBeTruthy()
  })

  it('renders type filter dropdown', async () => {
    renderWithProviders()
    await screen.findByText('Project Alpha')
    expect(screen.getByText('All Types')).toBeInTheDocument()
  })

  it('renders pagination info', async () => {
    renderWithProviders()
    expect(await screen.findByText(/Showing 1/)).toBeInTheDocument()
  })
})
