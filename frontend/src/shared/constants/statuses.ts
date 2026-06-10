export const PROJECT_STATUSES = ['ACTIVE', 'COMPLETED', 'ON_HOLD', 'CANCELLED'] as const
export type ProjectStatus = (typeof PROJECT_STATUSES)[number]

export const PROJECT_TYPES = ['FIXED_PRICE', 'TIME_AND_MATERIAL', 'CLIENT_ONBOARDING'] as const
export type ProjectType = (typeof PROJECT_TYPES)[number]

export const ASSIGNMENT_STATUSES = ['ACTIVE', 'RELEASED', 'AUTO_RELEASED'] as const
export type AssignmentStatus = (typeof ASSIGNMENT_STATUSES)[number]

export const ACCESS_LEVELS = ['NONE', 'VIEW', 'EDIT'] as const
export type AccessLevel = (typeof ACCESS_LEVELS)[number]

export const SCOPES = ['ALL', 'OWN_PORTFOLIO', 'SELF_ONLY'] as const
export type Scope = (typeof SCOPES)[number]
