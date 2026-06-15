import api from '../../shared/lib/axios'

export interface AssignmentResource {
  id: string
  name: string
  designation: string | null
  technical_expertise: string | null
}

export interface AssignmentListItem {
  id: string
  project_id: string
  resource: AssignmentResource | null
  effective_designation: string | null
  effective_expertise: string | null
  allocation_pct: number
  billability_pct: number | null
  is_shadow: boolean | null
  billing_rate: number | null
  project_designation: string | null
  project_expertise: string | null
  start_date: string
  end_date: string | null
  status: string
  released_at: string | null
  created_at: string | null
}

export interface AssignmentCreatePayload {
  resource_id: string
  allocation_pct: number
  billability_pct: number
  is_shadow: boolean
  project_designation?: string | null
  project_expertise?: string | null
  start_date: string
  end_date?: string | null
}

export interface AssignmentUpdatePayload {
  allocation_pct?: number
  billability_pct?: number
  is_shadow?: boolean
  project_designation?: string | null
  project_expertise?: string | null
  start_date?: string
  end_date?: string | null
}

export async function fetchProjectAssignments(
  projectId: string,
  status?: string,
): Promise<{ data: AssignmentListItem[] }> {
  const params = new URLSearchParams()
  if (status) params.set('status', status)
  const { data } = await api.get(`/projects/${projectId}/assignments?${params.toString()}`)
  return data
}

export async function fetchResourceAssignments(
  resourceId: string,
  status?: string,
): Promise<{ data: AssignmentListItem[] }> {
  const params = new URLSearchParams()
  if (status) params.set('status', status)
  const { data } = await api.get(`/resources/${resourceId}/assignments?${params.toString()}`)
  return data
}

export async function createAssignment(
  projectId: string,
  payload: AssignmentCreatePayload,
): Promise<{ data: AssignmentListItem; warnings?: string[] }> {
  const { data } = await api.post(`/projects/${projectId}/assignments`, payload)
  return data
}

export async function updateAssignment(
  assignmentId: string,
  payload: AssignmentUpdatePayload,
): Promise<{ data: AssignmentListItem; warnings?: string[] }> {
  const { data } = await api.put(`/assignments/${assignmentId}`, payload)
  return data
}

export async function releaseAssignment(
  assignmentId: string,
): Promise<{ data: AssignmentListItem }> {
  const { data } = await api.post(`/assignments/${assignmentId}/release`)
  return data
}

export async function fetchAssignment(
  assignmentId: string,
): Promise<{ data: AssignmentListItem }> {
  const { data } = await api.get(`/assignments/${assignmentId}`)
  return data
}
