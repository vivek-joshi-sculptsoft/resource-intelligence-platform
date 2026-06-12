import { create } from 'zustand'
import { getMeApi, loginApi, logoutApi, type User } from './api'

interface AuthState {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  setUser: (user: User) => void
  clearUser: () => void
  setLoading: (loading: boolean) => void
  login: (email: string, password: string) => Promise<void>
  logout: () => Promise<void>
  restoreSession: () => Promise<void>
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: false,
  isLoading: true,

  setUser: (user) => set({ user, isAuthenticated: true, isLoading: false }),
  clearUser: () => set({ user: null, isAuthenticated: false, isLoading: false }),
  setLoading: (isLoading) => set({ isLoading }),

  login: async (email, password) => {
    const { user } = await loginApi(email, password)
    set({ user, isAuthenticated: true, isLoading: false })
  },

  logout: async () => {
    await logoutApi()
    set({ user: null, isAuthenticated: false, isLoading: false })
  },

  restoreSession: async () => {
    try {
      const user = await getMeApi()
      set({ user, isAuthenticated: true, isLoading: false })
    } catch {
      set({ user: null, isAuthenticated: false, isLoading: false })
    }
  },
}))
