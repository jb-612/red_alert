import { describe, it, expect } from 'vitest'
import { useLocaleStore } from '@/store/locale'

describe('labels', () => {
  it('should import labels module without error', async () => {
    const mod = await import('../labels')
    expect(mod.useLabels).toBeDefined()
    expect(typeof mod.useLabels).toBe('function')
  })

  it('should have consistent lang state', () => {
    const { lang } = useLocaleStore.getState()
    expect(['en', 'he']).toContain(lang)
  })
})
