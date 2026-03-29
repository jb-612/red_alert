import { describe, it, expect } from 'vitest'
import { useThemeStore } from '../theme'

describe('useThemeStore', () => {
  it('should have a dark property', () => {
    const state = useThemeStore.getState()
    expect(typeof state.dark).toBe('boolean')
  })

  it('should toggle dark mode', () => {
    const initial = useThemeStore.getState().dark
    useThemeStore.getState().toggle()
    expect(useThemeStore.getState().dark).toBe(!initial)
    // Toggle back to restore
    useThemeStore.getState().toggle()
    expect(useThemeStore.getState().dark).toBe(initial)
  })

  it('should have a toggle function', () => {
    expect(typeof useThemeStore.getState().toggle).toBe('function')
  })
})
