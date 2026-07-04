import api from '../../shared/lib/axios'

export interface WorklogProjectRef {
  id: string
  name: string
}

export interface WorklogResourceRef {
  id: string
  name: string
}

export interface WorklogEntry {
  id: string
  project: WorklogProjectRef
  resource: WorklogResourceRef
  log_date: string
  hours: number
  note: string | null
  created_at: string
}

export interface WorklogCreatePayload {
  project_id: string
  log_date: string
  hours: number
  note?: string | null
}

export interface WorklogUpdatePayload {
  hours?: number
  note?: string | null
}

export interface WorklogListResponse {
  data: WorklogEntry[]
  total: number
  page: number
  limit: number
}

export async function fetchMyWorklogs(params?: {
  project_id?: string
  start_date?: string
  end_date?: string
  page?: number
  limit?: number
}): Promise<WorklogListResponse> {
  const qs = new URLSearchParams()
  if (params?.project_id) qs.set('project_id', params.project_id)
  if (params?.start_date) qs.set('start_date', params.start_date)
  if (params?.end_date) qs.set('end_date', params.end_date)
  if (params?.page) qs.set('page', String(params.page))
  if (params?.limit) qs.set('limit', String(params.limit))
  const { data } = await api.get(`/worklogs/my?${qs.toString()}`)
  return data
}

export async function createWorklog(payload: WorklogCreatePayload): Promise<{ data: WorklogEntry }> {
  const { data } = await api.post('/worklogs', payload)
  return data
}

export async function updateWorklog(
  id: string,
  payload: WorklogUpdatePayload,
): Promise<{ data: WorklogEntry }> {
  const { data } = await api.put(`/worklogs/${id}`, payload)
  return data
}

export async function deleteWorklog(id: string): Promise<{ success: boolean }> {
  const { data } = await api.delete(`/worklogs/${id}`)
  return data
}

export async function fetchAllWorklogs(params?: {
  client_id?: string
  project_id?: string
  resource_id?: string
  start_date?: string
  end_date?: string
  page?: number
  limit?: number
}): Promise<WorklogListResponse> {
  const qs = new URLSearchParams()
  if (params?.client_id) qs.set('client_id', params.client_id)
  if (params?.project_id) qs.set('project_id', params.project_id)
  if (params?.resource_id) qs.set('resource_id', params.resource_id)
  if (params?.start_date) qs.set('start_date', params.start_date)
  if (params?.end_date) qs.set('end_date', params.end_date)
  if (params?.page) qs.set('page', String(params.page))
  if (params?.limit) qs.set('limit', String(params.limit))
  const { data } = await api.get(`/worklogs?${qs.toString()}`)
  return data
}

export async function fetchProjectWorklogs(
  projectId: string,
  params?: {
    resource_id?: string
    start_date?: string
    end_date?: string
    page?: number
    limit?: number
  },
): Promise<WorklogListResponse> {
  const qs = new URLSearchParams()
  if (params?.resource_id) qs.set('resource_id', params.resource_id)
  if (params?.start_date) qs.set('start_date', params.start_date)
  if (params?.end_date) qs.set('end_date', params.end_date)
  if (params?.page) qs.set('page', String(params.page))
  if (params?.limit) qs.set('limit', String(params.limit))
  const { data } = await api.get(`/projects/${projectId}/worklogs?${qs.toString()}`)
  return data
}

function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  a.remove()
  URL.revokeObjectURL(url)
}

function extractFilename(headers: Record<string, string>, fallback: string): string {
  const disposition = headers['content-disposition'] ?? ''
  const match = disposition.match(/filename="?([^";\n]+)"?/)
  return match?.[1] ?? fallback
}

export async function exportAllWorklogs(params?: {
  client_id?: string
  project_id?: string
  resource_id?: string
  start_date?: string
  end_date?: string
}): Promise<void> {
  const qs = new URLSearchParams()
  if (params?.client_id) qs.set('client_id', params.client_id)
  if (params?.project_id) qs.set('project_id', params.project_id)
  if (params?.resource_id) qs.set('resource_id', params.resource_id)
  if (params?.start_date) qs.set('start_date', params.start_date)
  if (params?.end_date) qs.set('end_date', params.end_date)
  const resp = await api.get(`/worklogs/export?${qs.toString()}`, { responseType: 'blob' })
  downloadBlob(resp.data, extractFilename(resp.headers as Record<string, string>, 'worklogs.xlsx'))
}

export async function exportMyWorklogs(params?: {
  project_id?: string
  start_date?: string
  end_date?: string
}): Promise<void> {
  const qs = new URLSearchParams()
  if (params?.project_id) qs.set('project_id', params.project_id)
  if (params?.start_date) qs.set('start_date', params.start_date)
  if (params?.end_date) qs.set('end_date', params.end_date)
  const resp = await api.get(`/worklogs/my/export?${qs.toString()}`, { responseType: 'blob' })
  downloadBlob(resp.data, extractFilename(resp.headers as Record<string, string>, 'my_worklogs.xlsx'))
}

export async function exportProjectWorklogs(
  projectId: string,
  params?: {
    resource_id?: string
    start_date?: string
    end_date?: string
  },
): Promise<void> {
  const qs = new URLSearchParams()
  if (params?.resource_id) qs.set('resource_id', params.resource_id)
  if (params?.start_date) qs.set('start_date', params.start_date)
  if (params?.end_date) qs.set('end_date', params.end_date)
  const resp = await api.get(`/projects/${projectId}/worklogs/export?${qs.toString()}`, { responseType: 'blob' })
  downloadBlob(resp.data, extractFilename(resp.headers as Record<string, string>, 'project_worklogs.xlsx'))
}
