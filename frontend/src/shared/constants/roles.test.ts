import { describe, it, expect } from 'vitest'
import { ROLE_CODES, ROLE_HIERARCHY } from './roles'

describe('role constants', () => {
  it('defines all 7 roles', () => {
    expect(Object.keys(ROLE_CODES)).toHaveLength(7)
  })

  it('CEO has highest permission level', () => {
    expect(ROLE_HIERARCHY.CEO).toBe(100)
  })

  it('ENGINEER has lowest permission level', () => {
    expect(ROLE_HIERARCHY.ENGINEER).toBe(10)
  })

  it('all roles have a hierarchy value', () => {
    for (const code of Object.values(ROLE_CODES)) {
      expect(ROLE_HIERARCHY[code]).toBeDefined()
    }
  })
})
