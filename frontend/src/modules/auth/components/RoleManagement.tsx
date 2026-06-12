import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import api from '../../../shared/lib/axios'

interface Permission {
  data_type: string
  access_level: string
  scope: string
  is_configurable: boolean
}

interface RoleWithPermissions {
  id: string
  code: string
  name: string
  permission_level: number
  is_active: boolean
  permissions: Permission[]
}

const DATA_TYPE_LABELS: Record<string, string> = {
  client_profiles: 'Client Profiles',
  project_details: 'Project Details',
  resource_profiles: 'Resource Profiles',
  allocation: 'Allocation',
  billability: 'Billability',
  billing_rates: 'Billing Rates',
  ctc_loaded_cost: 'CTC / Loaded Cost',
  project_margin: 'Project Margin',
  non_human_costs: 'Non-Human Costs',
  shadow_assignments: 'Shadow Assignments',
  resource_availability: 'Resource Availability',
  bench_data: 'Bench Data',
  invoicing: 'Invoicing',
  worklogs: 'Worklogs',
  alerts: 'Alerts',
}

const ACCESS_BADGE_STYLES: Record<string, { bg: string; color: string }> = {
  EDIT: { bg: '#d1fae5', color: '#065f46' },
  VIEW: { bg: '#dbeafe', color: '#1e40af' },
  NONE: { bg: '#f1f5f9', color: '#64748b' },
}

const SCOPE_BADGE_STYLES: Record<string, { bg: string; color: string }> = {
  ALL: { bg: '#ede9fe', color: '#5b21b6' },
  OWN_PORTFOLIO: { bg: '#fef3c7', color: '#92400e' },
  SELF_ONLY: { bg: '#f1f5f9', color: '#64748b' },
}

function primaryScope(permissions: Permission[]): string {
  const scopeCount: Record<string, number> = {}
  permissions.forEach((p) => {
    if (p.scope) scopeCount[p.scope] = (scopeCount[p.scope] || 0) + 1
  })
  let best = 'ALL'
  let bestN = 0
  for (const s in scopeCount) {
    if (scopeCount[s] > bestN) { bestN = scopeCount[s]; best = s }
  }
  return best
}

export function RoleManagement() {
  const [selectedRoleId, setSelectedRoleId] = useState<string | null>(null)

  const { data, isLoading } = useQuery({
    queryKey: ['roles-with-permissions'],
    queryFn: async () => {
      const { data } = await api.get<{ data: RoleWithPermissions[] }>('/roles')
      return data.data
    },
  })

  const roles = data ?? []
  const selectedRole = roles.find((r) => r.id === selectedRoleId)

  return (
    <div>
      {/* Breadcrumb */}
      <div className="mb-1.5 text-[13px]" style={{ color: '#7C85C0' }}>
        <span style={{ color: '#4A5BB5' }}>Settings</span>
        <span style={{ color: '#7C85C0' }}> &rsaquo; </span>
        <span style={{ color: '#7C85C0' }}>Roles</span>
      </div>

      <h1 className="mb-5 text-[22px] font-bold" style={{ color: '#1e1b4b' }}>Role Management</h1>

      {isLoading ? (
        <div className="py-8 text-center text-[13.5px]" style={{ color: '#7C85C0' }}>Loading...</div>
      ) : (
        <div className="flex items-start gap-5">
          {/* Left Panel — Role List */}
          <div
            className="w-[280px] shrink-0 overflow-hidden rounded-xl"
            style={{ background: '#fff', boxShadow: '0 2px 8px rgba(43,57,144,0.06), 0 1px 3px rgba(0,0,0,0.04)', border: '1px solid #E8EAF6' }}
          >
            <div className="px-5 pb-3 pt-4" style={{ borderBottom: '1px solid #E8EAF6' }}>
              <h3 className="text-[15px] font-bold" style={{ color: '#1e1b4b' }}>Roles ({roles.length})</h3>
            </div>
            <div className="p-2">
              {roles.map((role) => {
                const isSelected = selectedRoleId === role.id
                return (
                  <div
                    key={role.id}
                    onClick={() => setSelectedRoleId(role.id)}
                    className="mb-0.5 flex cursor-pointer items-center justify-between rounded-lg px-3.5 py-3 transition-all"
                    style={{
                      background: isSelected ? 'rgba(43,57,144,0.08)' : 'transparent',
                      border: isSelected ? '1.5px solid #2B3990' : '1.5px solid transparent',
                    }}
                    onMouseEnter={(e) => { if (!isSelected) (e.currentTarget as HTMLElement).style.background = '#F0F1FA' }}
                    onMouseLeave={(e) => { if (!isSelected) (e.currentTarget as HTMLElement).style.background = 'transparent' }}
                  >
                    <div className="flex flex-col gap-0.5">
                      <span className="text-[14px] font-semibold" style={{ color: isSelected ? '#2B3990' : '#1e1b4b' }}>
                        {role.name}
                      </span>
                      <span className="text-[11.5px]" style={{ color: '#6b7280' }}>{role.code}</span>
                    </div>
                    <span
                      className="rounded-[10px] px-2.5 py-[3px] text-[11px] font-semibold"
                      style={{
                        background: isSelected ? '#2B3990' : '#F0F1FA',
                        color: isSelected ? '#fff' : '#7C85C0',
                        border: isSelected ? '1px solid #2B3990' : '1px solid #E8EAF6',
                      }}
                    >
                      {role.permission_level}
                    </span>
                  </div>
                )
              })}
            </div>
          </div>

          {/* Right Panel — Permission Matrix */}
          <div
            className="min-w-0 flex-1 overflow-hidden rounded-xl"
            style={{ background: '#fff', boxShadow: '0 2px 8px rgba(43,57,144,0.06), 0 1px 3px rgba(0,0,0,0.04)', border: '1px solid #E8EAF6' }}
          >
            {selectedRole ? (
              <>
                {/* Header */}
                <div className="px-6 pb-3.5 pt-4" style={{ borderBottom: '1px solid #E8EAF6' }}>
                  <h3 className="mb-1 text-[15px] font-bold" style={{ color: '#1e1b4b' }}>
                    Permissions &mdash; {selectedRole.name}
                  </h3>
                  <div className="text-[13px]" style={{ color: '#6b7280' }}>
                    Permission Level: {selectedRole.permission_level} &nbsp;|&nbsp; Scope: {primaryScope(selectedRole.permissions)}
                  </div>
                </div>

                {/* Info Banner */}
                <div
                  className="mx-6 mt-4 flex items-center gap-2.5 rounded-lg px-4 py-2.5 text-[13px]"
                  style={{ background: '#eff6ff', border: '1px solid #bfdbfe', color: '#1e40af' }}
                >
                  <span
                    className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full text-[12px] font-bold"
                    style={{ background: '#bfdbfe', color: '#1e40af' }}
                  >
                    i
                  </span>
                  Editing permissions will be available in Phase 3.
                </div>

                {/* Permission Table */}
                <div className="overflow-x-auto px-6 pb-6 pt-4">
                  <table
                    className="w-full overflow-hidden rounded-[10px] text-[13.5px]"
                    style={{ borderCollapse: 'separate', borderSpacing: 0, border: '1px solid #D6DAF0' }}
                  >
                    <thead>
                      <tr>
                        {['Data Type', 'Access Level', 'Scope', 'Configurable'].map((h, i) => (
                          <th
                            key={h}
                            className="whitespace-nowrap border-none px-4 py-3 text-left text-[12px] font-semibold uppercase tracking-wide text-white"
                            style={{
                              background: 'linear-gradient(135deg, #2B3990, #4A5BB5)',
                              paddingLeft: i === 0 ? '20px' : undefined,
                              width: ['35%', '22%', '25%', '18%'][i],
                              letterSpacing: '0.05em',
                            }}
                          >
                            {h}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {selectedRole.permissions.map((p) => {
                        const accessStyle = ACCESS_BADGE_STYLES[p.access_level] ?? ACCESS_BADGE_STYLES.NONE
                        const scopeStyle = p.scope ? SCOPE_BADGE_STYLES[p.scope] ?? SCOPE_BADGE_STYLES.ALL : null
                        return (
                          <tr
                            key={p.data_type}
                            className="transition-colors"
                            style={{ borderBottom: '1px solid #E8EAF6' }}
                            onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.background = '#F0F1FA' }}
                            onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.background = '' }}
                          >
                            <td className="whitespace-nowrap px-4 py-[11px] pl-5 font-medium" style={{ color: '#1e1b4b' }}>
                              {DATA_TYPE_LABELS[p.data_type] || p.data_type}
                            </td>
                            <td className="whitespace-nowrap px-4 py-[11px]">
                              <span
                                className="inline-flex items-center rounded-md px-2.5 py-[3px] text-[12px] font-semibold"
                                style={{ background: accessStyle.bg, color: accessStyle.color, letterSpacing: '0.02em' }}
                              >
                                {p.access_level}
                              </span>
                            </td>
                            <td className="whitespace-nowrap px-4 py-[11px]">
                              {scopeStyle ? (
                                <span
                                  className="inline-flex items-center rounded-md px-2.5 py-[3px] text-[12px] font-semibold"
                                  style={{ background: scopeStyle.bg, color: scopeStyle.color, letterSpacing: '0.02em' }}
                                >
                                  {p.scope}
                                </span>
                              ) : (
                                <span style={{ color: '#cbd5e1' }}>&mdash;</span>
                              )}
                            </td>
                            <td className="whitespace-nowrap px-4 py-[11px]">
                              {p.is_configurable ? (
                                <span className="text-[16px] font-bold" style={{ color: '#22c55e' }}>&#10003;</span>
                              ) : (
                                <span className="text-[16px]" style={{ color: '#cbd5e1' }}>&mdash;</span>
                              )}
                            </td>
                          </tr>
                        )
                      })}
                    </tbody>
                  </table>
                </div>
              </>
            ) : (
              <div className="flex flex-col items-center justify-center py-16 text-center">
                <div
                  className="mb-4 flex h-14 w-14 items-center justify-center rounded-full text-[24px]"
                  style={{ background: '#F0F1FA', color: '#7C85C0' }}
                >
                  &#128272;
                </div>
                <p className="text-[14px]" style={{ color: '#6b7280' }}>Select a role to view its permissions.</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
