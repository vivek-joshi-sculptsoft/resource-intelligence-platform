import { describe, it, expect, beforeEach } from 'vitest'
import { useAuthStore } from './store'

describe('useAuthStore', () => {
  beforeEach(() => {
    useAuthStore.setState({
      user: null,
      isAuthenticated: false,
      isLoading: true,
    })
  })

  it('starts unauthenticated', () => {
    const state = useAuthStore.getState()
    expect(state.isAuthenticated).toBe(false)
    expect(state.user).toBeNull()
  })

  it('sets user and marks authenticated', () => {
    const mockUser = {
      id: '1',
      email: 'ceo@test.com',
      name: 'Test CEO',
      role: { code: 'CEO', name: 'CEO', permission_level: 100 },
      resource_id: null,
    }
    useAuthStore.getState().setUser(mockUser)

    const state = useAuthStore.getState()
    expect(state.isAuthenticated).toBe(true)
    expect(state.user?.email).toBe('ceo@test.com')
    expect(state.isLoading).toBe(false)
  })

  it('clears user on logout', () => {
    useAuthStore.getState().setUser({
      id: '1',
      email: 'ceo@test.com',
      name: 'Test CEO',
      role: { code: 'CEO', name: 'CEO', permission_level: 100 },
      resource_id: null,
    })
    useAuthStore.getState().clearUser()

    const state = useAuthStore.getState()
    expect(state.isAuthenticated).toBe(false)
    expect(state.user).toBeNull()
  })
})
