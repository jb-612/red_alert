import { describe, it, expect } from 'vitest'
import { useLocaleStore } from '../locale'

describe('useLocaleStore', () => {
  it('should have lang and dir properties', () => {
    const state = useLocaleStore.getState()
    expect(['en', 'he']).toContain(state.lang)
    expect(['ltr', 'rtl']).toContain(state.dir)
  })

  it('should toggle between en and he', () => {
    const initial = useLocaleStore.getState().lang
    useLocaleStore.getState().toggleLang()
    const toggled = useLocaleStore.getState()
    expect(toggled.lang).not.toBe(initial)

    if (initial === 'en') {
      expect(toggled.lang).toBe('he')
      expect(toggled.dir).toBe('rtl')
    } else {
      expect(toggled.lang).toBe('en')
      expect(toggled.dir).toBe('ltr')
    }

    // Toggle back to restore
    useLocaleStore.getState().toggleLang()
    expect(useLocaleStore.getState().lang).toBe(initial)
  })

  it('should have matching dir for lang', () => {
    const { lang, dir } = useLocaleStore.getState()
    if (lang === 'he') expect(dir).toBe('rtl')
    if (lang === 'en') expect(dir).toBe('ltr')
  })
})
