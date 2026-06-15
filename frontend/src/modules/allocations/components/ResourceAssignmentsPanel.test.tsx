import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router'
import { ResourceAssignmentsPanel } from './ResourceAssignmentsPanel'
import { useAuthStore } from '../../auth/store'

vi.mock('../api', () => ({
  fetchResourceAssignments: vi.fn().mockImplementation((_id: string, status?: string) => {
    if (status === 'ACTIVE') {
      return Promise.resolve({
        data: [
          {
            id: 'a1',
            project_id: 'p1',
            project: { id: 'p1', name: 'TechCorp ERP', type: 'FIXED_PRICE', status: 'ACTIVE' },
            resource: { id: 'r1', name: 'Arjun Mehta', designation: 'Sr. Engineer', technical_expertise: 'React' },
            effective_designation: 'Frontend Lead',
            effective_expertise: 'React',
            allocation_pct: 50,
            billability_pct: 50,
            is_shadow: false,
            billing_rate: null,
            project_designation: 'Frontend Lead',
            project_expertise: null,
            start_date: '2026-01-01',
            end_date: '2026-06-30',
            status: 'ACTIVE',
            released_at: null,
            created_at: '2026-01-01T00:00:00Z',
          },
          {
            id: 'a2',
            project_id: 'p2',
            project: { id: 'p2', name: 'FinServ Analytics', type: 'TIME_AND_MATERIAL', status: 'ACTIVE' },
            resource: { id: 'r1', name: 'Arjun Mehta', designation: 'Sr. Engineer', technical_expertise: 'React' },
            effective_designation: 'Senior Developer',
            effective_expertise: null,
            allocation_pct: 60,
            billability_pct: 40,
            is_shadow: false,
            billing_rate: null,
            project_designation: 'Senior Developer',
            project_expertise: null,
            start_date: '2026-02-15',
            end_date: null,
            status: 'ACTIVE',
            released_at: null,
            created_at: '2026-02-15T00:00:00Z',
          },
        ],
      })
    }
    return Promise.resolve({
      data: [
        {
          id: 'a3',
          project_id: 'p3',
          project: { id: 'p3', name: 'RetailMax Inventory', type: 'FIXED_PRICE', status: 'COMPLETED' },
          resource: { id: 'r1', name: 'Arjun Mehta', designation: 'Sr. Engineer', technical_expertise: 'React' },
          effective_designation: 'Frontend Developer',
          effective_expertise: null,
          allocation_pct: 100,
          billability_pct: 80,
          is_shadow: false,
          billing_rate: null,
          project_designation: 'Frontend Developer',
          project_expertise: null,
          start_date: '2024-03-01',
          end_date: '2025-12-31',
          status: 'RELEASED',
          released_at: '2025-12-31T00:00:00Z',
          created_at: '2024-03-01T00:00:00Z',
        },
      ],
    })
  }),
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
        <ResourceAssignmentsPanel resourceId="r1" />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('ResourceAssignmentsPanel', () => {
  beforeEach(() => {
    setRole('CEO')
  })

  it('renders active assignments', async () => {
    renderWithProviders()
    expect(await screen.findByText('Frontend Lead')).toBeInTheDocument()
    expect(screen.getByText('Senior Developer')).toBeInTheDocument()
  })

  it('shows read-only note', async () => {
    renderWithProviders()
    expect(await screen.findByText(/read-only view/)).toBeInTheDocument()
  })

  it('shows total allocation footer', async () => {
    renderWithProviders()
    await screen.findByText('Frontend Lead')
    expect(screen.getByText('Total Allocation')).toBeInTheDocument()
    expect(screen.getByText('110%')).toBeInTheDocument()
  })

  it('shows Show History button', async () => {
    renderWithProviders()
    await screen.findByText('Frontend Lead')
    expect(screen.getByText('Show History')).toBeInTheDocument()
  })

  it('loads history when Show History clicked', async () => {
    renderWithProviders()
    await screen.findByText('Frontend Lead')
    fireEvent.click(screen.getByText('Show History'))
    await waitFor(() => {
      expect(screen.getByText('Hide History')).toBeInTheDocument()
    })
  })

  it('hides billability for HR', async () => {
    setRole('HR')
    renderWithProviders()
    await screen.findByText('Frontend Lead')
    expect(screen.queryByText('Billability %')).not.toBeInTheDocument()
  })

  it('shows billability for CEO', async () => {
    renderWithProviders()
    await screen.findByText('Frontend Lead')
    expect(screen.getByText('Billability %')).toBeInTheDocument()
  })

  it('shows Ongoing for null end date', async () => {
    renderWithProviders()
    await screen.findByText('Frontend Lead')
    expect(screen.getByText('Ongoing')).toBeInTheDocument()
  })
})

describe('ResourceAssignmentsPanel — empty state', () => {
  beforeEach(async () => {
    setRole('CEO')
    const api = await import('../api')
    vi.mocked(api.fetchResourceAssignments).mockResolvedValueOnce({ data: [] })
  })

  it('shows bench message when no active assignments', async () => {
    renderWithProviders()
    await waitFor(() => {
      expect(screen.getByText('No active assignments')).toBeInTheDocument()
      expect(screen.getByText('This resource is currently on bench.')).toBeInTheDocument()
    })
  })
})
