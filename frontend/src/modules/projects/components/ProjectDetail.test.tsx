import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter, Routes, Route } from 'react-router'
import { ProjectDetail } from './ProjectDetail'
import { useAuthStore } from '../../auth/store'

vi.mock('../api', () => ({
  fetchProject: vi.fn().mockResolvedValue({
    data: {
      id: 'proj-1',
      name: 'Project Phoenix',
      client: { id: 'c1', name: 'Acme Corp' },
      type: 'FIXED_PRICE',
      status: 'ACTIVE',
      billing_currency: 'INR',
      contract_value: null,
      start_date: '2026-01-01',
      contract_end_date: '2026-12-31',
      dm: { id: 'r1', name: 'Rajesh' },
      pm: { id: 'r2', name: 'Priya' },
      worklog_enabled: true,
      notes: null,
      created_at: '2026-01-01T00:00:00Z',
    },
  }),
  transitionProjectStatus: vi.fn().mockResolvedValue({ data: {} }),
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
      <MemoryRouter initialEntries={['/projects/proj-1']}>
        <Routes>
          <Route path="/projects/:id" element={<ProjectDetail />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('ProjectDetail', () => {
  beforeEach(() => {
    setRole('CEO')
  })

  it('renders project header with client name', async () => {
    renderWithProviders()
    await waitFor(() => {
      expect(screen.getByText('Acme Corp')).toBeInTheDocument()
    })
  })

  it('renders tabs including worklogs when enabled', async () => {
    renderWithProviders()
    await waitFor(() => {
      expect(screen.getByText('Acme Corp')).toBeInTheDocument()
    })
    expect(screen.getAllByText('Assignments').length).toBeGreaterThan(0)
    expect(screen.getByText('Worklogs')).toBeInTheDocument()
    expect(screen.getByText('Financials')).toBeInTheDocument()
  })

  it('switches tabs on click', async () => {
    renderWithProviders()
    await waitFor(() => {
      expect(screen.getByText('Financials')).toBeInTheDocument()
    })
    fireEvent.click(screen.getByText('Financials'))
    expect(screen.getByText(/Phase 2/)).toBeInTheDocument()
  })

  it('shows transition buttons for CEO', async () => {
    renderWithProviders()
    await waitFor(() => {
      expect(screen.getByText('Complete')).toBeInTheDocument()
    })
    expect(screen.getByText('Put on Hold')).toBeInTheDocument()
  })

  it('hides transition buttons for ENGINEER', async () => {
    setRole('ENGINEER')
    renderWithProviders()
    await waitFor(() => {
      expect(screen.getByText('Acme Corp')).toBeInTheDocument()
    })
    expect(screen.queryByText('Complete')).not.toBeInTheDocument()
  })

  it('shows confirmation dialog on transition click', async () => {
    renderWithProviders()
    await waitFor(() => {
      expect(screen.getByText('Complete')).toBeInTheDocument()
    })
    fireEvent.click(screen.getByText('Complete'))
    expect(screen.getByText(/Are you sure/)).toBeInTheDocument()
  })

  it('shows edit button for CEO', async () => {
    renderWithProviders()
    await waitFor(() => {
      expect(screen.getByText('Edit')).toBeInTheDocument()
    })
  })
})
