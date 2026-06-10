export const ROLE_CODES = {
  CEO: 'CEO',
  CTO: 'CTO',
  DM: 'DM',
  PM: 'PM',
  FINANCE: 'FINANCE',
  HR: 'HR',
  ENGINEER: 'ENGINEER',
} as const

export type RoleCode = (typeof ROLE_CODES)[keyof typeof ROLE_CODES]

export const ROLE_HIERARCHY: Record<RoleCode, number> = {
  CEO: 100,
  CTO: 90,
  FINANCE: 70,
  DM: 70,
  PM: 60,
  HR: 50,
  ENGINEER: 10,
}
