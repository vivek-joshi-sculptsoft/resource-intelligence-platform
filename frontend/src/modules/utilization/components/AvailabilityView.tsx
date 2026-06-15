import { useState, useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router'
import {
  fetchAvailability,
  type AvailabilityData,
  type AvailabilityBenchResource,
  type AvailabilityPartialResource,
  type AvailabilityReleasingSoon,
  type AvailabilityFullyAllocated,
} from '../api'

type FilterTab = 'all' | 'bench' | 'partial' | 'releasing_soon' | 'fully_allocated'

interface UnifiedRow {
  id: string | null
  name: string
  designation: string
  allocationPct: number
  availablePct: number
  status: 'bench' | 'partial' | 'fully' | 'over' | 'releasing'
  statusLabel: string
  projects: string[]
  details: React.ReactNode
  bucket: FilterTab
}

function benchDaysClass(days: number): string {
  if (days > 14) return 'text-[#ef4444] font-bold'
  if (days > 7) return 'text-[#f59e0b] font-bold'
  return 'text-[#22c55e] font-bold'
}

function allocBarColor(pct: number, bucket: string): { fill: string; text: string } {
  if (bucket === 'bench') return { fill: '#22c55e', text: '#22c55e' }
  if (bucket === 'releasing') return { fill: '#f59e0b', text: '#f59e0b' }
  if (pct > 100) return { fill: '#ef4444', text: '#ef4444' }
  if (pct === 100) return { fill: '#9CA3AF', text: '#6B7280' }
  if (pct >= 50) return { fill: '#f59e0b', text: '#f59e0b' }
  return { fill: '#22c55e', text: '#22c55e' }
}

function availBarColor(pct: number): { fill: string; text: string } {
  if (pct <= 0) return { fill: '#9CA3AF', text: '#6B7280' }
  if (pct > 50) return { fill: '#22c55e', text: '#22c55e' }
  return { fill: '#f59e0b', text: '#f59e0b' }
}

function buildRows(data: AvailabilityData): UnifiedRow[] {
  const rows: UnifiedRow[] = []

  data.bench.forEach((r: AvailabilityBenchResource) => {
    rows.push({
      id: r.id,
      name: r.name,
      designation: r.designation,
      allocationPct: 0,
      availablePct: 100,
      status: 'bench',
      statusLabel: 'On Bench',
      projects: [],
      details: (
        <span className={benchDaysClass(r.days_on_bench)}>
          {r.days_on_bench}d on bench
        </span>
      ),
      bucket: 'bench',
    })
  })

  data.partial.forEach((r: AvailabilityPartialResource) => {
    rows.push({
      id: r.id,
      name: r.name,
      designation: r.designation,
      allocationPct: r.total_allocation_pct,
      availablePct: r.spare_capacity_pct,
      status: 'partial',
      statusLabel: 'Partial',
      projects: r.projects,
      details: null,
      bucket: 'partial',
    })
  })

  data.fully_allocated.forEach((r: AvailabilityFullyAllocated) => {
    const isOver = r.total_allocation_pct > 100
    rows.push({
      id: r.id,
      name: r.name,
      designation: r.designation,
      allocationPct: r.total_allocation_pct,
      availablePct: isOver ? -(r.total_allocation_pct - 100) : 0,
      status: isOver ? 'over' : 'fully',
      statusLabel: isOver ? 'Over-Allocated' : 'Fully Allocated',
      projects: r.projects,
      details: null,
      bucket: 'fully_allocated',
    })
  })

  data.releasing_soon.forEach((r: AvailabilityReleasingSoon) => {
    rows.push({
      id: r.resource_id,
      name: r.name,
      designation: r.designation,
      allocationPct: r.allocation_pct,
      availablePct: 0,
      status: 'releasing',
      statusLabel: 'Releasing Soon',
      projects: [r.project_name],
      details: (
        <div className="text-[12px]">
          <div className="text-[#7C85C0]">
            {new Date(r.end_date).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })}
          </div>
          <div className={r.days_remaining <= 7 ? 'text-[#ef4444] font-semibold' : r.days_remaining <= 14 ? 'text-[#f59e0b] font-semibold' : 'text-[#6b7280] font-semibold'}>
            {r.days_remaining}d remaining
          </div>
        </div>
      ),
      bucket: 'releasing_soon',
    })
  })

  return rows
}

const STATUS_CONFIG: Record<string, { dotClass: string; textClass: string; label: string }> = {
  bench: { dotClass: 'bg-[#22c55e] shadow-[0_0_6px_rgba(34,197,94,0.4)]', textClass: 'text-[#166534]', label: 'On Bench' },
  partial: { dotClass: 'bg-[#f59e0b] shadow-[0_0_6px_rgba(245,158,11,0.4)]', textClass: 'text-[#92400E]', label: 'Partial' },
  fully: { dotClass: 'bg-[#9CA3AF]', textClass: 'text-[#6B7280]', label: 'Fully Allocated' },
  over: { dotClass: 'bg-[#ef4444] shadow-[0_0_6px_rgba(239,68,68,0.4)] animate-pulse', textClass: 'text-[#B91C1C]', label: 'Over-Allocated' },
  releasing: { dotClass: 'bg-[#f59e0b] shadow-[0_0_6px_rgba(245,158,11,0.4)]', textClass: 'text-[#92400E]', label: 'Releasing Soon' },
}

const WINDOW_OPTIONS = [30, 60, 90] as const

function AllocationBar({ pct, color }: { pct: number; color: { fill: string; text: string } }) {
  return (
    <div className="flex items-center gap-2">
      <div className="w-[80px] h-[8px] bg-[#E5E7EB] rounded flex-shrink-0 overflow-hidden">
        <div
          className="h-full rounded"
          style={{ width: `${Math.min(Math.abs(pct), 100)}%`, background: color.fill }}
        />
      </div>
      <span className="font-bold text-[13px] min-w-[40px]" style={{ color: color.text }}>
        {pct < 0 ? `${pct}%` : `${pct}%`}
      </span>
    </div>
  )
}

function LoadingSkeleton() {
  return (
    <div className="animate-pulse space-y-5">
      <div className="flex gap-6">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="h-14 w-40 rounded-lg bg-[#E8EAF6]" />
        ))}
      </div>
      <div className="h-10 w-72 rounded-lg bg-[#E8EAF6]" />
      <div className="h-80 rounded-xl bg-[#E8EAF6]" />
    </div>
  )
}

export function AvailabilityView() {
  const navigate = useNavigate()
  const [activeFilter, setActiveFilter] = useState<FilterTab>('all')
  const [search, setSearch] = useState('')
  const [window, setWindow] = useState<number>(30)

  const { data, isLoading, error } = useQuery({
    queryKey: ['dashboard', 'availability', window],
    queryFn: () => fetchAvailability(window),
  })

  const rows = useMemo(() => (data ? buildRows(data) : []), [data])

  const filtered = useMemo(() => {
    let result = rows
    if (activeFilter !== 'all') {
      result = result.filter((r) => r.bucket === activeFilter)
    }
    if (search.trim()) {
      const q = search.toLowerCase()
      result = result.filter((r) => r.name.toLowerCase().includes(q))
    }
    return result
  }, [rows, activeFilter, search])

  const counts = useMemo(() => {
    if (!data) return { bench: 0, partial: 0, releasing_soon: 0, fully_allocated: 0, over: 0, all: 0 }
    const overCount = data.fully_allocated.filter((r) => r.total_allocation_pct > 100).length
    return {
      bench: data.bench.length,
      partial: data.partial.length,
      releasing_soon: data.releasing_soon.length,
      fully_allocated: data.fully_allocated.length - overCount,
      over: overCount,
      all: rows.length,
    }
  }, [data, rows])

  if (isLoading) return <LoadingSkeleton />
  if (error) return <div className="text-center py-12 text-[#ef4444]">Failed to load availability data</div>
  if (!data) return null

  const TABS: { key: FilterTab; label: string; count: number }[] = [
    { key: 'all', label: 'All', count: counts.all },
    { key: 'bench', label: 'Bench', count: counts.bench },
    { key: 'partial', label: 'Partial', count: counts.partial },
    { key: 'releasing_soon', label: 'Releasing Soon', count: counts.releasing_soon },
    { key: 'fully_allocated', label: 'Fully Allocated', count: counts.fully_allocated + counts.over },
  ]

  return (
    <div>
      {/* Summary Strip */}
      <div className="flex gap-6 mb-5">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-[#22c55e]" />
          <div>
            <div className="text-[15px] font-bold text-[#1e1b4b]">{counts.bench}</div>
            <div className="text-[13px] text-[#6b7280]">On Bench</div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-[#f59e0b]" />
          <div>
            <div className="text-[15px] font-bold text-[#1e1b4b]">{counts.partial}</div>
            <div className="text-[13px] text-[#6b7280]">Partial</div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-[#9CA3AF]" />
          <div>
            <div className="text-[15px] font-bold text-[#1e1b4b]">{counts.fully_allocated}</div>
            <div className="text-[13px] text-[#6b7280]">Fully Allocated</div>
          </div>
        </div>
        {counts.over > 0 && (
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-[#ef4444]" />
            <div>
              <div className="text-[15px] font-bold text-[#1e1b4b]">{counts.over}</div>
              <div className="text-[13px] text-[#6b7280]">Over-Allocated</div>
            </div>
          </div>
        )}
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-[#f59e0b]" />
          <div>
            <div className="text-[15px] font-bold text-[#1e1b4b]">{counts.releasing_soon}</div>
            <div className="text-[13px] text-[#6b7280]">Releasing Soon</div>
          </div>
        </div>
      </div>

      {/* Toolbar: Search + Filters + Window Toggle */}
      <div className="flex items-center justify-between mb-5 gap-3">
        <div className="relative">
          <span className="absolute left-3 top-1/2 -translate-y-1/2 text-[#7C85C0] text-[14px]">&#128269;</span>
          <input
            type="text"
            placeholder="Search by resource name..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="py-2 pl-9 pr-3.5 border rounded-lg text-[13px] w-[280px] focus:outline-none focus:border-[#2B3990] focus:shadow-[0_0_0_3px_rgba(43,57,144,0.08)]"
            style={{ borderColor: '#D6DAF0', fontFamily: 'inherit' }}
          />
        </div>
        <div className="flex items-center gap-3">
          <div className="flex gap-2">
            {TABS.map((tab) => (
              <button
                key={tab.key}
                onClick={() => setActiveFilter(tab.key)}
                className={`px-3.5 py-[7px] text-[12px] font-medium border rounded-full cursor-pointer transition-all inline-flex items-center gap-1.5 ${
                  activeFilter === tab.key
                    ? 'bg-[#2B3990] text-white border-[#2B3990]'
                    : 'bg-white text-[#6b7280] border-[#D6DAF0] hover:border-[#2B3990] hover:text-[#2B3990]'
                }`}
                style={{ fontFamily: 'inherit' }}
              >
                {tab.label}
                <span
                  className={`px-[7px] py-px rounded-[10px] text-[11px] font-bold ${
                    activeFilter === tab.key
                      ? 'bg-white/30'
                      : 'bg-[#F5F6FC] text-[#7C85C0]'
                  }`}
                >
                  {tab.count}
                </span>
              </button>
            ))}
          </div>
          {/* Window toggle */}
          <div className="flex items-center gap-1 ml-2 border-l border-[#D6DAF0] pl-3">
            <span className="text-[11px] text-[#7C85C0] font-semibold uppercase tracking-wide mr-1">Window</span>
            {WINDOW_OPTIONS.map((w) => (
              <button
                key={w}
                onClick={() => setWindow(w)}
                className={`px-2.5 py-1 text-[11px] font-semibold rounded cursor-pointer transition-all ${
                  window === w
                    ? 'bg-[#2B3990] text-white'
                    : 'bg-[#F5F6FC] text-[#7C85C0] hover:bg-[#E8EAF6]'
                }`}
                style={{ border: 'none', fontFamily: 'inherit' }}
              >
                {w}d
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Table */}
      {filtered.length === 0 ? (
        <div className="text-center py-16">
          <div className="text-[48px] mb-4">&#128100;</div>
          <h3 className="text-[16px] font-semibold text-[#1e1b4b] mb-1.5">No resources found</h3>
          <p className="text-[13px] text-[#6b7280]">Adjust your search or filter criteria to find resources.</p>
        </div>
      ) : (
        <div
          className="rounded-xl border border-[#E8EAF6] bg-white overflow-hidden"
          style={{ boxShadow: '0 2px 8px rgba(43,57,144,0.06), 0 1px 3px rgba(0,0,0,0.04)' }}
        >
          <table className="w-full border-collapse">
            <thead>
              <tr>
                {['Resource Name', 'Designation', 'Allocation', 'Available', 'Status', 'Projects', 'Details'].map((h) => (
                  <th
                    key={h}
                    className="px-4 py-3 text-left text-[12px] font-semibold uppercase tracking-wide text-white whitespace-nowrap"
                    style={{ background: 'linear-gradient(135deg, #2B3990 0%, #4A5BB5 100%)' }}
                  >
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filtered.map((row, i) => {
                const allocColor = allocBarColor(row.allocationPct, row.status)
                const availColor = availBarColor(row.availablePct)
                const cfg = STATUS_CONFIG[row.status]
                return (
                  <tr
                    key={`${row.name}-${row.bucket}-${i}`}
                    className={`border-b border-[#E8EAF6] transition-colors hover:bg-[#F0F1FA] ${
                      i % 2 === 1 ? 'bg-[#F5F6FC]' : ''
                    }`}
                  >
                    <td className="px-4 py-3 text-[13px]">
                      {row.id ? (
                        <button
                          onClick={() => navigate(`/resources/${row.id}`)}
                          className="font-semibold text-[#1e1b4b] hover:text-[#2B3990] bg-transparent border-none cursor-pointer text-left p-0"
                          style={{ fontFamily: 'inherit', fontSize: '13px' }}
                        >
                          {row.name}
                        </button>
                      ) : (
                        <span className="font-semibold text-[#1e1b4b]">{row.name}</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-[13px] text-[#6b7280]">{row.designation}</td>
                    <td className="px-4 py-3">
                      <AllocationBar pct={row.allocationPct} color={allocColor} />
                    </td>
                    <td className="px-4 py-3">
                      <AllocationBar pct={row.availablePct} color={availColor} />
                    </td>
                    <td className="px-4 py-3">
                      <span className={`inline-flex items-center gap-1.5 font-semibold text-[12px] ${cfg.textClass}`}>
                        <span className={`w-2.5 h-2.5 rounded-full inline-block ${cfg.dotClass}`} />
                        {cfg.label}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      {row.projects.length > 0 ? (
                        row.projects.map((p) => (
                          <span
                            key={p}
                            className="inline-flex px-2 py-0.5 rounded-[10px] text-[11px] bg-[#F5F6FC] text-[#6b7280] mr-1 mb-0.5"
                          >
                            {p}
                          </span>
                        ))
                      ) : (
                        <span className="text-[#7C85C0] italic text-[12px]">No active projects</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-[12px]">{row.details}</td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
