import { useState, useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router'
import { fetchAvailability, type AvailabilityData } from '../api'

type TabKey = 'bench' | 'partial' | 'releasing_soon' | 'fully_allocated'

const WINDOW_OPTIONS = [30, 60, 90] as const

function formatInr(value: number | null | undefined): string {
  if (value === null || value === undefined) return '—'
  return `₹${Math.round(value).toLocaleString('en-IN')}`
}

function benchDaysBadgeClass(days: number): string {
  if (days > 14) return 'bg-[#fecaca] text-[#991b1b]'
  if (days > 7) return 'bg-[#fef3c7] text-[#92400e]'
  return 'bg-[#dcfce7] text-[#166534]'
}

function countdownClass(daysRemaining: number): string {
  if (daysRemaining <= 7) return 'text-[#ef4444]'
  if (daysRemaining <= 14) return 'text-[#f59e0b]'
  return 'text-[#6b7280]'
}

function AllocBar({ pct }: { pct: number }) {
  const fill = pct > 100 ? '#ef4444' : pct === 100 ? '#9CA3AF' : '#f59e0b'
  return (
    <div className="flex items-center justify-center gap-2">
      <div className="w-[60px] h-[8px] bg-[#E5E7EB] rounded overflow-hidden flex-shrink-0">
        <div className="h-full rounded" style={{ width: `${Math.min(pct, 100)}%`, background: fill }} />
      </div>
      <span className="font-bold text-[13px]" style={{ color: pct > 100 ? '#ef4444' : '#1e1b4b' }}>
        {pct}%
      </span>
    </div>
  )
}

function ProjectPills({ projects }: { projects: string[] }) {
  if (projects.length === 0) {
    return <span className="text-[#7C85C0] italic text-[12px]">No active projects</span>
  }
  return (
    <>
      {projects.map((p) => (
        <span
          key={p}
          className="inline-flex px-2 py-0.5 rounded-[10px] text-[11px] bg-[#F5F6FC] text-[#6b7280] mr-1 mb-0.5"
        >
          {p}
        </span>
      ))}
    </>
  )
}

function ResourceLink({ id, name, navigate }: { id: string; name: string; navigate: (path: string) => void }) {
  return (
    <button
      onClick={() => navigate(`/resources/${id}`)}
      className="font-semibold text-[#1e1b4b] hover:text-[#2B3990] bg-transparent border-none cursor-pointer text-left p-0"
      style={{ fontFamily: 'inherit', fontSize: '13px' }}
    >
      {name}
    </button>
  )
}

function EmptyRow({ colSpan, message }: { colSpan: number; message: string }) {
  return (
    <tr>
      <td colSpan={colSpan} className="text-center py-12">
        <div className="text-[40px] mb-3">&#128100;</div>
        <div className="text-[14px] text-[#6b7280]">{message}</div>
      </td>
    </tr>
  )
}

function TableHeader({ columns }: { columns: { label: string; align?: 'left' | 'center' | 'right' }[] }) {
  return (
    <thead>
      <tr>
        {columns.map((c) => (
          <th
            key={c.label}
            className={`px-4 py-3 text-[12px] font-semibold uppercase tracking-wide text-white whitespace-nowrap ${
              c.align === 'center' ? 'text-center' : c.align === 'right' ? 'text-right' : 'text-left'
            }`}
            style={{ background: 'linear-gradient(135deg, #2B3990 0%, #4A5BB5 100%)' }}
          >
            {c.label}
          </th>
        ))}
      </tr>
    </thead>
  )
}

function LoadingSkeleton() {
  return (
    <div className="animate-pulse space-y-5">
      <div className="grid grid-cols-4 gap-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="h-20 rounded-xl bg-[#E8EAF6]" />
        ))}
      </div>
      <div className="h-10 w-72 rounded-lg bg-[#E8EAF6]" />
      <div className="h-80 rounded-xl bg-[#E8EAF6]" />
    </div>
  )
}

const SUMMARY_CARD_CONFIG: Record<TabKey, { label: string; sub: string; barColor: string }> = {
  bench: { label: 'On Bench', sub: '0% allocated', barColor: 'linear-gradient(90deg, #ef4444, #f87171)' },
  partial: { label: 'Partially Available', sub: '<100% allocated', barColor: 'linear-gradient(90deg, #f59e0b, #fbbf24)' },
  releasing_soon: { label: 'Releasing Soon', sub: 'Ending within window', barColor: 'linear-gradient(90deg, #2B3990, #4A5BB5)' },
  fully_allocated: { label: 'Fully Allocated', sub: '100%+ allocated', barColor: 'linear-gradient(90deg, #22c55e, #4ade80)' },
}

const TAB_LABELS: Record<TabKey, string> = {
  bench: 'Bench',
  partial: 'Partially Available',
  releasing_soon: 'Releasing Soon',
  fully_allocated: 'Fully Allocated',
}

export function AvailabilityView() {
  const navigate = useNavigate()
  const [activeTab, setActiveTab] = useState<TabKey>('bench')
  const [search, setSearch] = useState('')
  const [window, setWindow] = useState<number>(30)

  const { data, isLoading, error } = useQuery({
    queryKey: ['dashboard', 'availability', window],
    queryFn: () => fetchAvailability(window),
  })

  const counts = useMemo(() => {
    if (!data) return { bench: 0, partial: 0, releasing_soon: 0, fully_allocated: 0 }
    return {
      bench: data.bench.length,
      partial: data.partial.length,
      releasing_soon: data.releasing_soon.length,
      fully_allocated: data.fully_allocated.length,
    }
  }, [data])

  const filteredData = useMemo(() => {
    if (!data) return null
    const q = search.trim().toLowerCase()
    if (!q) return data
    const filterByName = <T extends { name: string }>(items: T[]) =>
      items.filter((item) => item.name.toLowerCase().includes(q))
    return {
      ...data,
      bench: filterByName(data.bench),
      partial: filterByName(data.partial),
      releasing_soon: filterByName(data.releasing_soon),
      fully_allocated: filterByName(data.fully_allocated),
    } satisfies AvailabilityData
  }, [data, search])

  if (isLoading) return <LoadingSkeleton />
  if (error) return <div className="text-center py-12 text-[#ef4444]">Failed to load availability data</div>
  if (!data || !filteredData) return null

  const dailyBenchBurn = data.bench.reduce((sum, r) => sum + (r.bench_cost_daily ?? 0), 0)

  const TABS: TabKey[] = ['bench', 'partial', 'releasing_soon', 'fully_allocated']

  return (
    <div>
      {/* Summary Cards */}
      <div className="grid grid-cols-4 gap-4 mb-5">
        {TABS.map((tab) => {
          const cfg = SUMMARY_CARD_CONFIG[tab]
          return (
            <div
              key={tab}
              className="relative rounded-xl border border-[#E8EAF6] bg-white p-5 overflow-hidden"
              style={{ boxShadow: '0 2px 8px rgba(43,57,144,0.06), 0 1px 3px rgba(0,0,0,0.04)' }}
            >
              <div className="absolute top-0 left-0 right-0 h-1" style={{ background: cfg.barColor }} />
              <div className="text-[28px] font-extrabold text-[#1e1b4b]">{counts[tab]}</div>
              <div className="text-[13px] font-semibold text-[#6b7280] mt-1">{cfg.label}</div>
              <div className="text-[12px] text-[#7C85C0] mt-0.5">{cfg.sub}</div>
            </div>
          )
        })}
      </div>

      {/* Bench Cost Summary — restricted to CEO/CTO/Finance */}
      {data.can_see_bench_cost && data.total_bench_cost_monthly !== null && (
        <div
          className="flex items-center justify-between rounded-xl px-6 py-5 mb-5 text-white"
          style={{
            background: 'linear-gradient(135deg, #1B2B65, #2B3990)',
            boxShadow: '0 4px 12px rgba(43,57,144,0.3)',
          }}
        >
          <div>
            <div className="text-[13px] font-medium opacity-80">Total Monthly Bench Cost</div>
            <div className="text-[28px] font-extrabold mt-1">{formatInr(data.total_bench_cost_monthly)}</div>
            <div className="text-[12px] opacity-70 mt-0.5">{counts.bench} resources on bench</div>
          </div>
          <div className="text-right">
            <div className="text-[11px] uppercase tracking-wide opacity-70">Daily Bench Burn</div>
            <div className="text-[18px] font-bold mt-0.5">{formatInr(dailyBenchBurn)} /day</div>
          </div>
        </div>
      )}

      {/* Tabbed Section */}
      <div
        className="rounded-xl border border-[#E8EAF6] bg-white overflow-hidden"
        style={{ boxShadow: '0 2px 8px rgba(43,57,144,0.06), 0 1px 3px rgba(0,0,0,0.04)' }}
      >
        {/* Tab Bar */}
        <div className="flex border-b-2 border-[#E8EAF6]">
          {TABS.map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-5 py-3 text-[14px] font-medium cursor-pointer border-b-2 -mb-px flex items-center gap-2 transition-colors ${
                activeTab === tab
                  ? 'text-[#FF4B2B] border-[#FF4B2B] font-semibold'
                  : 'text-[#6b7280] border-transparent hover:text-[#1e1b4b]'
              }`}
              style={{ fontFamily: 'inherit', background: 'none' }}
            >
              {TAB_LABELS[tab]}
              <span
                className={`inline-flex items-center justify-center min-w-[22px] h-[22px] px-1.5 rounded-[11px] text-[11px] font-bold ${
                  activeTab === tab ? 'bg-[#FFF0EC] text-[#FF4B2B]' : 'bg-[#F5F6FC] text-[#7C85C0]'
                }`}
              >
                {counts[tab]}
              </span>
            </button>
          ))}
        </div>

        {/* Search Bar */}
        <div className="flex items-center gap-3 px-5 py-3 border-b border-[#E8EAF6]">
          <div className="relative max-w-[320px] flex-1">
            <span className="absolute left-3 top-1/2 -translate-y-1/2 text-[#7C85C0] text-[14px]">&#128269;</span>
            <input
              type="text"
              placeholder="Search by resource name..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full py-2 pl-9 pr-3.5 border rounded-lg text-[13px] focus:outline-none focus:border-[#2B3990] focus:shadow-[0_0_0_3px_rgba(43,57,144,0.08)]"
              style={{ borderColor: '#D6DAF0', fontFamily: 'inherit' }}
            />
          </div>
        </div>

        {/* Day Window Filter — Releasing Soon tab only */}
        {activeTab === 'releasing_soon' && (
          <div className="flex items-center gap-2 px-5 py-3 bg-[#F5F6FC] border-b border-[#E8EAF6]">
            <span className="text-[13px] text-[#6b7280] font-medium">Show releasing within:</span>
            {WINDOW_OPTIONS.map((w) => (
              <button
                key={w}
                onClick={() => setWindow(w)}
                className={`px-3.5 py-1.5 text-[12px] font-semibold rounded-full cursor-pointer transition-colors ${
                  window === w
                    ? 'bg-[#2B3990] text-white border border-[#2B3990]'
                    : 'bg-white text-[#6b7280] border border-[#D6DAF0] hover:border-[#2B3990] hover:text-[#2B3990]'
                }`}
                style={{ fontFamily: 'inherit' }}
              >
                {w} Days
              </button>
            ))}
          </div>
        )}

        {/* Bench Tab */}
        {activeTab === 'bench' && (
          <table className="w-full border-collapse">
            <TableHeader
              columns={[
                { label: 'Resource' },
                { label: 'Designation' },
                { label: 'Expertise' },
                { label: 'Days on Bench', align: 'center' },
                { label: 'Tags' },
                ...(data.can_see_bench_cost
                  ? [
                      { label: 'Bench Cost (Daily)', align: 'right' as const },
                      { label: 'Bench Cost (Total)', align: 'right' as const },
                    ]
                  : []),
              ]}
            />
            <tbody>
              {filteredData.bench.length === 0 ? (
                <EmptyRow colSpan={data.can_see_bench_cost ? 7 : 5} message="No resources currently on bench." />
              ) : (
                filteredData.bench.map((r, i) => (
                  <tr
                    key={r.id}
                    className={`border-b border-[#E8EAF6] hover:bg-[#F0F1FA] ${i % 2 === 1 ? 'bg-[#F5F6FC]' : ''}`}
                  >
                    <td className="px-4 py-3"><ResourceLink id={r.id} name={r.name} navigate={navigate} /></td>
                    <td className="px-4 py-3 text-[13px] text-[#6b7280]">{r.designation}</td>
                    <td className="px-4 py-3 text-[13px] text-[#6b7280]">{r.technical_expertise ?? '—'}</td>
                    <td className="px-4 py-3 text-center">
                      <span className={`inline-flex px-2.5 py-1 rounded-full text-[12px] font-bold ${benchDaysBadgeClass(r.days_on_bench)}`}>
                        {r.days_on_bench} days
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      {r.tags.map((t) => (
                        <span key={t} className="inline-flex px-2 py-0.5 rounded-[10px] text-[11px] bg-[#F5F6FC] text-[#6b7280] mr-1 mb-0.5">
                          {t}
                        </span>
                      ))}
                    </td>
                    {data.can_see_bench_cost && (
                      <>
                        <td className="px-4 py-3 text-right text-[13px] font-semibold text-[#1e1b4b]">
                          {formatInr(r.bench_cost_daily)}
                        </td>
                        <td className="px-4 py-3 text-right text-[13px] font-semibold text-[#1e1b4b]">
                          {formatInr(r.bench_cost_total)}
                        </td>
                      </>
                    )}
                  </tr>
                ))
              )}
            </tbody>
          </table>
        )}

        {/* Partially Available Tab */}
        {activeTab === 'partial' && (
          <table className="w-full border-collapse">
            <TableHeader
              columns={[
                { label: 'Resource' },
                { label: 'Designation' },
                { label: 'Total Allocation', align: 'center' },
                { label: 'Spare Capacity', align: 'center' },
                { label: 'Current Projects' },
              ]}
            />
            <tbody>
              {filteredData.partial.length === 0 ? (
                <EmptyRow colSpan={5} message="No partially available resources." />
              ) : (
                filteredData.partial.map((r, i) => (
                  <tr
                    key={r.id}
                    className={`border-b border-[#E8EAF6] hover:bg-[#F0F1FA] ${i % 2 === 1 ? 'bg-[#F5F6FC]' : ''}`}
                  >
                    <td className="px-4 py-3"><ResourceLink id={r.id} name={r.name} navigate={navigate} /></td>
                    <td className="px-4 py-3 text-[13px] text-[#6b7280]">{r.designation}</td>
                    <td className="px-4 py-3"><AllocBar pct={r.total_allocation_pct} /></td>
                    <td className="px-4 py-3 text-center text-[13px] font-bold text-[#22c55e]">
                      {r.spare_capacity_pct}%
                    </td>
                    <td className="px-4 py-3"><ProjectPills projects={r.projects} /></td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        )}

        {/* Releasing Soon Tab */}
        {activeTab === 'releasing_soon' && (
          <table className="w-full border-collapse">
            <TableHeader
              columns={[
                { label: 'Resource' },
                { label: 'Project' },
                { label: 'Allocation', align: 'center' },
                { label: 'Release Date' },
                { label: 'Days Remaining', align: 'center' },
              ]}
            />
            <tbody>
              {filteredData.releasing_soon.length === 0 ? (
                <EmptyRow colSpan={5} message={`No resources releasing in the next ${window} days.`} />
              ) : (
                filteredData.releasing_soon.map((r, i) => (
                  <tr
                    key={`${r.resource_id}-${r.project_name}`}
                    className={`border-b border-[#E8EAF6] hover:bg-[#F0F1FA] ${i % 2 === 1 ? 'bg-[#F5F6FC]' : ''}`}
                  >
                    <td className="px-4 py-3"><ResourceLink id={r.resource_id} name={r.name} navigate={navigate} /></td>
                    <td className="px-4 py-3 text-[13px] text-[#6b7280]">{r.project_name}</td>
                    <td className="px-4 py-3 text-center text-[13px] font-semibold text-[#1e1b4b]">{r.allocation_pct}%</td>
                    <td className="px-4 py-3 text-[13px] text-[#6b7280]">
                      {new Date(r.end_date).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })}
                    </td>
                    <td className={`px-4 py-3 text-center text-[13px] font-bold ${countdownClass(r.days_remaining)}`}>
                      {r.days_remaining} days
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        )}

        {/* Fully Allocated Tab */}
        {activeTab === 'fully_allocated' && (
          <table className="w-full border-collapse">
            <TableHeader
              columns={[
                { label: 'Resource' },
                { label: 'Designation' },
                { label: 'Total Allocation', align: 'center' },
                { label: 'Projects' },
              ]}
            />
            <tbody>
              {filteredData.fully_allocated.length === 0 ? (
                <EmptyRow colSpan={4} message="No fully allocated resources." />
              ) : (
                filteredData.fully_allocated.map((r, i) => (
                  <tr
                    key={r.id}
                    className={`border-b border-[#E8EAF6] hover:bg-[#F0F1FA] ${i % 2 === 1 ? 'bg-[#F5F6FC]' : ''}`}
                  >
                    <td className="px-4 py-3"><ResourceLink id={r.id} name={r.name} navigate={navigate} /></td>
                    <td className="px-4 py-3 text-[13px] text-[#6b7280]">{r.designation}</td>
                    <td className="px-4 py-3"><AllocBar pct={r.total_allocation_pct} /></td>
                    <td className="px-4 py-3"><ProjectPills projects={r.projects} /></td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
