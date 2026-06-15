import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router'
import { AssignmentFormModal } from './AssignmentFormModal'
import { useAuthStore } from '../../auth/store'

vi.mock('../api', () => ({
  createAssignment: vi.fn().mockResolvedValue({ data: { id: 'new-1' } }),
  updateAssignment: vi.fn().mockResolvedValue({ data: { id: 'a1' } }),
  fetchAssignment: vi.fn().mockResolvedValue({ data: null }),
}))

vi.mock('../../resources/api', () => ({
  fetchResources: vi.fn().mockResolvedValue({
    data: [
      { id: 'r1', employee_id: 'SS-001', name: 'Arjun Mehta', designation: 'Sr. Engineer', technical_expertise: 'React', total_allocation_pct: 70, is_active: true, tags: [], loaded_cost_monthly: null },
      { id: 'r2', employee_id: 'SS-002', name: 'Priya Patel', designation: 'Backend Dev', technical_expertise: 'Python', total_allocation_pct: 30, is_active: true, tags: [], loaded_cost_monthly: null },
    ],
    meta: { page: 1, limit: 100, total: 2, total_pages: 1 },
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

function renderWithProviders(props?: Partial<React.ComponentProps<typeof AssignmentFormModal>>) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <AssignmentFormModal
          open={true}
          projectId="p1"
          projectName="Test Project"
          editingAssignment={null}
          onClose={vi.fn()}
          {...props}
        />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('AssignmentFormModal', () => {
  beforeEach(() => {
    setRole('CEO')
  })

  it('renders create form title', async () => {
    renderWithProviders()
    expect(screen.getByText('Add Assignment')).toBeInTheDocument()
  })

  it('renders project name', () => {
    renderWithProviders()
    expect(screen.getByText('Project: Test Project')).toBeInTheDocument()
  })

  it('shows required field labels', () => {
    renderWithProviders()
    expect(screen.getByText(/Resource/)).toBeInTheDocument()
    expect(screen.getByText(/Allocation %/)).toBeInTheDocument()
    expect(screen.getByText(/Billability %/)).toBeInTheDocument()
    expect(screen.getByText(/Start Date/)).toBeInTheDocument()
  })

  it('shows validation errors on empty submit', async () => {
    renderWithProviders()
    fireEvent.click(screen.getByText('Save Assignment'))
    expect(await screen.findByText('Resource is required')).toBeInTheDocument()
    expect(screen.getByText('Start date is required')).toBeInTheDocument()
  })

  it('shadow toggle disables billability and sets to 0', async () => {
    renderWithProviders()
    const checkbox = screen.getByRole('checkbox')
    fireEvent.click(checkbox)
    await waitFor(() => {
      const billInput = document.querySelector('input[type="number"][disabled]') as HTMLInputElement
      expect(billInput).toBeTruthy()
      expect(billInput.value).toBe('0')
    })
  })

  it('shows over-allocation warning when total > 100%', async () => {
    renderWithProviders()
    await waitFor(() => {
      expect(screen.getByText(/Arjun Mehta/)).toBeInTheDocument()
    })
    const resourceSelect = screen.getByRole('combobox')
    fireEvent.change(resourceSelect, { target: { value: 'r1' } })
    const allocInput = document.querySelectorAll('input[type="number"]')[0] as HTMLInputElement
    fireEvent.change(allocInput, { target: { value: '50' } })
    await waitFor(() => {
      expect(screen.getByText(/total allocation.*120%/i)).toBeInTheDocument()
    })
  })

  it('validates billability cannot exceed allocation', async () => {
    renderWithProviders()
    const inputs = document.querySelectorAll('input[type="number"]')
    fireEvent.change(inputs[0], { target: { value: '30' } })
    fireEvent.change(inputs[1], { target: { value: '50' } })
    const resourceSelect = screen.getByRole('combobox')
    fireEvent.change(resourceSelect, { target: { value: 'r2' } })
    const startInput = document.querySelector('input[type="date"]') as HTMLInputElement
    fireEvent.change(startInput, { target: { value: '2026-01-01' } })
    fireEvent.click(screen.getByText('Save Assignment'))
    expect(await screen.findByText('Billability cannot exceed allocation percentage')).toBeInTheDocument()
  })

  it('validates end date must be after start date', async () => {
    renderWithProviders()
    const dateInputs = document.querySelectorAll('input[type="date"]')
    fireEvent.change(dateInputs[0], { target: { value: '2026-06-01' } })
    fireEvent.change(dateInputs[1], { target: { value: '2026-01-01' } })
    const resourceSelect = screen.getByRole('combobox')
    fireEvent.change(resourceSelect, { target: { value: 'r2' } })
    const allocInput = document.querySelectorAll('input[type="number"]')[0]
    fireEvent.change(allocInput, { target: { value: '50' } })
    fireEvent.click(screen.getByText('Save Assignment'))
    expect(await screen.findByText('End date must be after start date')).toBeInTheDocument()
  })

  it('does not render when open is false', () => {
    renderWithProviders({ open: false })
    expect(screen.queryByText('Add Assignment')).not.toBeInTheDocument()
  })

  it('renders edit title when editing', () => {
    renderWithProviders({
      editingAssignment: {
        id: 'a1',
        project_id: 'p1',
        resource: { id: 'r1', name: 'Arjun Mehta', designation: 'Sr. Engineer', technical_expertise: 'React' },
        effective_designation: 'Frontend Lead',
        effective_expertise: null,
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
    })
    expect(screen.getByText('Edit Assignment')).toBeInTheDocument()
  })
})
