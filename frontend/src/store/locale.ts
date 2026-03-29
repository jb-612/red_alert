import { create } from 'zustand'

type Lang = 'en' | 'he'
type Dir = 'ltr' | 'rtl'

function resolveInitialLang(): Lang {
  const stored = localStorage.getItem('lang')
  if (stored === 'he' || stored === 'en') return stored
  return 'en'
}

interface LocaleState {
  lang: Lang
  dir: Dir
  toggleLang: () => void
}

const initialLang = resolveInitialLang()
const initialDir: Dir = initialLang === 'he' ? 'rtl' : 'ltr'
document.documentElement.dir = initialDir
document.documentElement.lang = initialLang

export const useLocaleStore = create<LocaleState>((set) => ({
  lang: initialLang,
  dir: initialDir,
  toggleLang: () =>
    set((state) => {
      const next: Lang = state.lang === 'en' ? 'he' : 'en'
      const dir: Dir = next === 'he' ? 'rtl' : 'ltr'
      localStorage.setItem('lang', next)
      document.documentElement.dir = dir
      document.documentElement.lang = next
      return { lang: next, dir }
    }),
}))
