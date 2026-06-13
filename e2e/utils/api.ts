import { type APIRequestContext } from "@playwright/test";

const API_BASE = "http://localhost:8000/api/v1";

export async function apiLogin(
  request: APIRequestContext,
  email = "admin@riplatform.com",
  password = "admin123"
) {
  const response = await request.post(`${API_BASE}/auth/login`, {
    data: { email, password },
  });
  return response;
}

export async function apiGet(
  request: APIRequestContext,
  path: string,
  params?: Record<string, string>
) {
  const url = new URL(`${API_BASE}${path}`);
  if (params) {
    Object.entries(params).forEach(([k, v]) => url.searchParams.set(k, v));
  }
  return request.get(url.toString());
}

export async function apiPost(
  request: APIRequestContext,
  path: string,
  data: unknown
) {
  return request.post(`${API_BASE}${path}`, { data });
}

export async function apiPut(
  request: APIRequestContext,
  path: string,
  data: unknown
) {
  return request.put(`${API_BASE}${path}`, { data });
}

export async function apiDelete(
  request: APIRequestContext,
  path: string
) {
  return request.delete(`${API_BASE}${path}`);
}
