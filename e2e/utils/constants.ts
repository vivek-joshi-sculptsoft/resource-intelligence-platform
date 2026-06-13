export const ROUTES = {
  login: "/login",
  dashboard: "/dashboard",
  resources: "/resources",
  clients: "/clients",
  projects: "/projects",
} as const;

export const TEST_TIMEOUT = {
  navigation: 10_000,
  animation: 1_000,
  api: 5_000,
} as const;
