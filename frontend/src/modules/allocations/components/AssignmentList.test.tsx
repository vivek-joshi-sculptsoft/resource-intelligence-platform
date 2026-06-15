import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router'
import { AssignmentList } from './AssignmentList'
import { useAuthStore } from '../../auth/store'

vi.mock('../api', () => ({
  fetchProjectAssignments: vi.fn().mockResolvedValue({
    data: [
      {
        id: 'a1',
        project_id: 'p1',
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
        project_id: 'p1',
        resource: { id: 'r2', name: 'Priya Patel', designation: 'Backend Lead', technical_expertise: 'Python' },
        effective_designation: 'Backend Lead',
        effective_expertise: 'Python',
        allocation_pct: 80,
        billability_pct: 80,
        is_shadow: false,
        billing_rate: null,
        project_designation: null,
        project_expertise: null,
        start_date: '2026-01-01',
        end_date: null,
        status: 'ACTIVE',
        released_at: null,
        created_at: '2026-01-01T00:00:00Z',
      },
    ],
  }),
  releaseAssignment: vi.fn().mockResolvedValue({ data: {} }),
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

function renderWithProviders(props?: { onAddAssignment?: () => void; onEditAssignment?: () => void }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <AssignmentList
          projectId="p1"
          onAddAssignment={props?.onAddAssignment ?? vi.fn()}
          onEditAssignment={props?.onEditAssignment ?? vi.fn()}
        />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('AssignmentList', () => {
  beforeEach(() => {
    setRole('CEO')
  })

  it('renders assignment rows with resource names', async () => {
    renderWithProviders()
    expect(await screen.findByText('Arjun Mehta')).toBeInTheDocument()
    expect(screen.getByText('Priya Patel')).toBeInTheDocument()
  })

  it('shows Add Assignment button for CEO', async () => {
    renderWithProviders()
    expect(await screen.findByText('+ Add Assignment')).toBeInTheDocument()
  })

  it('hides Add Assignment button for ENGINEER', async () => {
    setRole('ENGINEER')
    renderWithProviders()
    await screen.findByText('Arjun Mehta')
    expect(screen.queryByText('+ Add Assignment')).not.toBeInTheDocument()
  })

  it('hides billability column for HR role', async () => {
    setRole('HR')
    renderWithProviders()
    await screen.findByText('Arjun Mehta')
    expect(screen.queryByText('Billability %')).not.toBeInTheDocument()
  })

  it('shows billability column for CEO role', async () => {
    renderWithProviders()
    await screen.findByText('Arjun Mehta')
    expect(screen.getByText('Billability %')).toBeInTheDocument()
  })

  it('shows release button for active assignments when CEO', async () => {
    renderWithProviders()
    await screen.findByText('Arjun Mehta')
    const releaseButtons = screen.getAllByText('Release')
    expect(releaseButtons.length).toBe(2)
  })

  it('hides release button for ENGINEER', async () => {
    setRole('ENGINEER')
    renderWithProviders()
    await screen.findByText('Arjun Mehta')
    expect(screen.queryByText('Release')).not.toBeInTheDocument()
  })

  it('shows release confirmation dialog on Release click', async () => {
    renderWithProviders()
    await screen.findByText('Arjun Mehta')
    fireEvent.click(screen.getAllByText('Release')[0])
    expect(screen.getByText(/Are you sure you want to release Arjun Mehta/)).toBeInTheDocument()
  })

  it('shows Ongoing for null end date', async () => {
    renderWithProviders()
    await screen.findByText('Arjun Mehta')
    expect(screen.getByText('Ongoing')).toBeInTheDocument()
  })

  it('renders status filter dropdown', async () => {
    renderWithProviders()
    await screen.findByText('Arjun Mehta')
    expect(screen.getByDisplayValue('Active')).toBeInTheDocument()
  })

  it('calls onAddAssignment when Add Assignment clicked', async () => {
    const onAdd = vi.fn()
    renderWithProviders({ onAddAssignment: onAdd })
    await screen.findByText('+ Add Assignment')
    fireEvent.click(screen.getByText('+ Add Assignment'))
    expect(onAdd).toHaveBeenCalled()
  })
})
