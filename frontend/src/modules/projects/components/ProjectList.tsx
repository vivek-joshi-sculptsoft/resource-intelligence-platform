import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router'
import { Plus, Search } from 'lucide-react'
import { useAuthStore } from '../../auth/store'
import { fetchProjects, type ProjectListItem } from '../api'
import { fetchClients } from '../../clients/api'
import { StatusBadge, TypeBadge, Breadcrumb, DataTable } from '../../../shared/components'
import { useDocumentTitle } from '../../../shared/hooks/useDocumentTitle'
import { type ColumnDef } from '@tanstack/react-table'
import { differenceInDays, parseISO } from 'date-fns'

function isExpiringWithin30Days(dateStr: string | null): boolean {
  if (!dateStr) return false
  const diff = differenceInDays(parseISO(dateStr), new Date())
  return diff >= 0 && diff <= 30
}

const columns: ColumnDef<ProjectListItem, unknown>[] = [
  {
    accessorKey: 'name',
    header: 'Name',
    cell: ({ row }) => (
      <span className="font-semibold" style={{ color: '#2B3990' }}>
        {row.original.name}
      </span>
    ),
  },
  { accessorKey: 'client_name', header: 'Client' },
  {
    accessorKey: 'type',
    header: 'Type',
    cell: ({ row }) => <TypeBadge type={row.original.type} />,
  },
  {
    accessorKey: 'status',
    header: 'Status',
    cell: ({ row }) => <StatusBadge status={row.original.status} />,
  },
  {
    accessorKey: 'dm_name',
    header: 'DM',
    cell: ({ row }) => (
      <span style={{ color: '#6b7280' }}>{row.original.dm_name}</span>
    ),
  },
  {
    accessorKey: 'pm_name',
    header: 'PM',
    cell: ({ row }) => (
      <span style={{ color: '#6b7280' }}>{row.original.pm_name}</span>
    ),
  },
  {
    accessorKey: 'start_date',
    header: 'Start Date',
    cell: ({ row }) => (
      <span style={{ color: '#6b7280' }}>{row.original.start_date ?? '—'}</span>
    ),
  },
  {
    accessorKey: 'contract_end_date',
    header: 'Contract End',
    cell: ({ row }) => {
      const d = row.original.contract_end_date
      if (!d) return <span style={{ color: '#6b7280' }}>—</span>
      const expiring = isExpiringWithin30Days(d)
      return (
        <span className={expiring ? 'font-semibold' : ''} style={{ color: expiring ? '#ef4444' : '#6b7280' }}>
          {d}
        </span>
      )
    },
  },
]

export function ProjectList() {
  const navigate = useNavigate()
  const { user } = useAuthStore()
  const canCreate = user && ['CEO', 'CTO', 'DM'].includes(user.role.code)

  const [page, setPage] = useState(1)
  const [status, setStatus] = useState('ACTIVE')
  const [type, setType] = useState('')
  const [clientId, setClientId] = useState('')
  const [search, setSearch] = useState('')

  useDocumentTitle('Projects')

  const { data, isLoading } = useQuery({
    queryKey: ['projects', page, status, type, clientId, search],
    queryFn: () => fetchProjects({
      page,
      limit: 20,
      status: status === 'ALL' ? undefined : status,
      type: type || undefined,
      client_id: clientId || undefined,
      search: search || undefined,
    }),
  })

  const { data: clientsData } = useQuery({
    queryKey: ['clients-dropdown'],
    queryFn: () => fetchClients({ limit: 100, status: 'ACTIVE' }),
  })

  const projects = data?.data ?? []
  const meta = data?.meta

  const selectStyle = {
    border: '1px solid #D6DAF0',
    color: '#1e1b4b',
    background: '#F0F1FA',
    appearance: 'none' as const,
    backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%237C85C0' stroke-width='2'%3E%3Cpolyline points='6 9 12 15 18 9'%3E%3C/polyline%3E%3C/svg%3E")`,
    backgroundRepeat: 'no-repeat',
    backgroundPosition: 'right 12px center',
  }

  return (
    <div>
      <Breadcrumb items={[{ label: 'Projects' }]} />

      <div className="mb-5 flex items-center justify-between">
        <div>
          <h1 className="text-[22px] font-bold" style={{ color: '#1e1b4b' }}>Project Management</h1>
          <p className="mt-0.5 text-[13px]" style={{ color: '#6b7280' }}>Manage projects, deliverables, and allocations</p>
        </div>
        {canCreate && (
          <button
            onClick={() => navigate('/projects/new')}
            className="flex items-center gap-1.5 rounded-lg border-none px-[22px] py-2.5 text-[14px] font-semibold text-white transition-all hover:-translate-y-px"
            style={{ background: 'linear-gradient(135deg, #FF4B2B, #ff6a4d)', boxShadow: '0 2px 8px rgba(255,75,43,0.25)' }}
          >
            <Plus size={16} strokeWidth={2.5} />
            Add Project
          </button>
        )}
      </div>

      {/* Filter Bar */}
      <div
        className="mb-4 flex flex-wrap items-center gap-3 rounded-xl p-4 px-5"
        style={{ background: '#fff', boxShadow: '0 2px 8px rgba(43,57,144,0.06), 0 1px 3px rgba(0,0,0,0.04)' }}
      >
        <div className="relative min-w-[220px] flex-1">
          <Search
            size={16}
            className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2"
            style={{ color: '#7C85C0' }}
          />
          <input
            type="text"
            placeholder="Search by project name..."
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1) }}
            className="w-full rounded-lg py-[9px] pl-[38px] pr-3.5 text-[13.5px] outline-none transition-all"
            style={{ border: '1px solid #D6DAF0', color: '#1e1b4b', background: '#F0F1FA' }}
            onFocus={(e) => { e.target.style.borderColor = '#4A5BB5'; e.target.style.boxShadow = '0 0 0 3px rgba(43,57,144,0.1)'; e.target.style.background = '#fff' }}
            onBlur={(e) => { e.target.style.borderColor = '#D6DAF0'; e.target.style.boxShadow = 'none'; e.target.style.background = '#F0F1FA' }}
          />
        </div>
        <select
          value={status}
          onChange={(e) => { setStatus(e.target.value); setPage(1) }}
          className="cursor-pointer rounded-lg py-[9px] pl-3.5 pr-8 text-[13.5px] outline-none"
          style={selectStyle}
        >
          <option value="ALL">All Status</option>
          <option value="ACTIVE">Active</option>
          <option value="COMPLETED">Completed</option>
          <option value="ON_HOLD">On Hold</option>
          <option value="CANCELLED">Cancelled</option>
        </select>
        <select
          value={type}
          onChange={(e) => { setType(e.target.value); setPage(1) }}
          className="cursor-pointer rounded-lg py-[9px] pl-3.5 pr-8 text-[13.5px] outline-none"
          style={selectStyle}
        >
          <option value="">All Types</option>
          <option value="FIXED_PRICE">Fixed Price</option>
          <option value="TIME_AND_MATERIAL">Time & Material</option>
          <option value="CLIENT_ONBOARDING">Client Onboarding</option>
        </select>
        <select
          value={clientId}
          onChange={(e) => { setClientId(e.target.value); setPage(1) }}
          className="cursor-pointer rounded-lg py-[9px] pl-3.5 pr-8 text-[13.5px] outline-none"
          style={selectStyle}
        >
          <option value="">All Clients</option>
          {(clientsData?.data ?? []).map((c) => (
            <option key={c.id} value={c.id}>{c.name}</option>
          ))}
        </select>
      </div>

      <DataTable
        columns={columns}
        data={projects}
        meta={meta}
        page={page}
        onPageChange={setPage}
        onRowClick={(row) => navigate(`/projects/${row.id}`)}
        isLoading={isLoading}
        emptyIcon={'\u{1F4C2}'}
        emptyTitle="No projects found"
        emptyDescription="Try adjusting your filters or create a new project."
        emptyAction={
          canCreate ? (
            <button
              onClick={() => navigate('/projects/new')}
              className="flex items-center gap-1.5 rounded-lg border-none px-[22px] py-2.5 text-[14px] font-semibold text-white"
              style={{ background: 'linear-gradient(135deg, #FF4B2B, #ff6a4d)', boxShadow: '0 2px 8px rgba(255,75,43,0.25)' }}
            >
              <Plus size={16} strokeWidth={2.5} />
              Add Project
            </button>
          ) : undefined
        }
      />
    </div>
  )
}
