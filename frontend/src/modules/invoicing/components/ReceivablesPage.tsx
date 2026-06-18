// See FSD §6.3 — Outstanding receivables view (VRIP-98)
import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router'
import type { ColumnDef } from '@tanstack/react-table'
import { fetchReceivables, type Receivable } from '../api'
import { DataTable } from '../../../shared/components'
import { useDocumentTitle } from '../../../shared/hooks/useDocumentTitle'

function formatDate(iso: string): string {
  const d = new Date(iso + 'T00:00:00')
  return d.toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })
}

function formatInr(val: number): string {
  return '₹' + val.toLocaleString('en-IN', { minimumFractionDigits: 0, maximumFractionDigits: 0 })
}

function formatMoney(val: number, currency: string): string {
  return `${val.toLocaleString('en-IN', { minimumFractionDigits: 0, maximumFractionDigits: 2 })} ${currency}`
}

function daysOutstanding(invoiceDate: string): number {
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const inv = new Date(invoiceDate + 'T00:00:00')
  return Math.max(0, Math.round((today.getTime() - inv.getTime()) / 86_400_000))
}

const STATUS_BADGE_STYLES: Record<string, { bg: string; color: string }> = {
  DRAFT: { bg: '#f3f4f6', color: '#4b5563' },
  SUBMITTED: { bg: '#dbeafe', color: '#1e40af' },
  APPROVED: { bg: '#dcfce7', color: '#166534' },
}

export function ReceivablesPage() {
  useDocumentTitle('Receivables')
  const navigate = useNavigate()

  const [statusFilter, setStatusFilter] = useState('')
  const [projectFilter, setProjectFilter] = useState('')
  const [clientFilter, setClientFilter] = useState('')

  const { data, isLoading } = useQuery({
    queryKey: ['receivables', statusFilter],
    queryFn: () => fetchReceivables(statusFilter || undefined),
  })

  const receivables: Receivable[] = useMemo(() => data?.data ?? [], [data])

  const projectOptions = useMemo(
    () => Array.from(new Set(receivables.map((r) => r.project_name).filter(Boolean))) as string[],
    [receivables],
  )
  const clientOptions = useMemo(
    () => Array.from(new Set(receivables.map((r) => r.client_name).filter(Boolean))) as string[],
    [receivables],
  )

  const filtered = useMemo(
    () =>
      receivables.filter(
        (r) =>
          (!projectFilter || r.project_name === projectFilter) &&
          (!clientFilter || r.client_name === clientFilter),
      ),
    [receivables, projectFilter, clientFilter],
  )

  const totalOutstandingInr = useMemo(
    () => filtered.reduce((s, r) => s + (r.amount_inr ?? 0), 0),
    [filtered],
  )

  const columns: ColumnDef<Receivable, unknown>[] = [
    { id: 'project_name', header: 'Project', accessorFn: (r) => r.project_name ?? '—' },
    { id: 'client_name', header: 'Client', accessorFn: (r) => r.client_name ?? '—' },
    {
      id: 'invoice_date',
      header: 'Invoice Date',
      accessorFn: (r) => r.invoice_date,
      cell: ({ getValue }) => {
        const v = getValue<string | null>()
        return v ? formatDate(v) : '—'
      },
    },
    {
      id: 'amount',
      header: 'Amount',
      accessorFn: (r) => r.amount,
      cell: ({ row }) => (row.original.amount != null ? formatMoney(row.original.amount, row.original.currency) : '—'),
    },
    {
      id: 'amount_inr',
      header: 'Amount (INR)',
      accessorFn: (r) => r.amount_inr,
      cell: ({ getValue }) => {
        const v = getValue<number | null>()
        return v != null ? <strong>{formatInr(v)}</strong> : '—'
      },
    },
    {
      id: 'status',
      header: 'Status',
      accessorFn: (r) => r.status,
      cell: ({ getValue }) => {
        const status = getValue<string>()
        const s = STATUS_BADGE_STYLES[status] ?? STATUS_BADGE_STYLES.DRAFT
        return (
          <span
            style={{
              display: 'inline-flex', alignItems: 'center', gap: 4, padding: '4px 10px',
              borderRadius: 20, fontSize: 11, fontWeight: 700, textTransform: 'uppercase',
              letterSpacing: 0.5, background: s.bg, color: s.color,
            }}
          >
            {status}
          </span>
        )
      },
    },
    {
      id: 'days_outstanding',
      header: 'Days Outstanding',
      accessorFn: (r) => (r.invoice_date ? daysOutstanding(r.invoice_date) : 0),
      cell: ({ getValue }) => `${getValue<number>()} days`,
    },
  ]

  return (
    <div>
      <h1 className="mb-5 text-[22px] font-bold" style={{ color: '#1e1b4b' }}>Receivables</h1>

      {/* Summary */}
      <div
        className="mb-5 rounded-xl p-5"
        style={{
          background: '#fff', border: '1px solid #E8EAF6',
          boxShadow: '0 2px 8px rgba(43,57,144,0.06), 0 1px 3px rgba(0,0,0,0.04)',
        }}
      >
        <div className="text-[12px] font-semibold uppercase tracking-wide" style={{ color: '#7C85C0' }}>
          Total Outstanding
        </div>
        <div className="mt-1 text-[26px] font-bold" style={{ color: '#1e1b4b' }}>
          {formatInr(totalOutstandingInr)}
        </div>
        <div className="mt-1 text-[13px]" style={{ color: '#6b7280' }}>
          {filtered.length} invoice{filtered.length !== 1 ? 's' : ''} outstanding
        </div>
      </div>

      {/* Filters */}
      <div className="mb-4 flex items-center gap-3">
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          style={{
            padding: '6px 12px', fontSize: 13, border: '1px solid #D6DAF0', borderRadius: 8,
            color: '#1e1b4b', background: '#fff', cursor: 'pointer',
          }}
        >
          <option value="">All Statuses</option>
          <option value="SUBMITTED">Submitted</option>
          <option value="APPROVED">Approved</option>
        </select>

        <select
          value={projectFilter}
          onChange={(e) => setProjectFilter(e.target.value)}
          style={{
            padding: '6px 12px', fontSize: 13, border: '1px solid #D6DAF0', borderRadius: 8,
            color: '#1e1b4b', background: '#fff', cursor: 'pointer',
          }}
        >
          <option value="">All Projects</option>
          {projectOptions.map((p) => (
            <option key={p} value={p}>{p}</option>
          ))}
        </select>

        <select
          value={clientFilter}
          onChange={(e) => setClientFilter(e.target.value)}
          style={{
            padding: '6px 12px', fontSize: 13, border: '1px solid #D6DAF0', borderRadius: 8,
            color: '#1e1b4b', background: '#fff', cursor: 'pointer',
          }}
        >
          <option value="">All Clients</option>
          {clientOptions.map((c) => (
            <option key={c} value={c}>{c}</option>
          ))}
        </select>
      </div>

      <DataTable
        columns={columns}
        data={filtered}
        isLoading={isLoading}
        emptyIcon="💰"
        emptyTitle="No receivables"
        emptyDescription="There are no outstanding invoices to follow up on right now."
        onRowClick={(r) => navigate(`/projects/${r.project_id}?tab=invoices`)}
      />
    </div>
  )
}
