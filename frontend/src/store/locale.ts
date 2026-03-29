import { create } from 'zustand'

type Lang = 'en' | 'he'
type Dir = 'ltr' | 'rtl'

function resolveInitialLang(): Lang {
  try {
    const stored = localStorage.getItem('lang')
    if (stored === 'he' || stored === 'en') return stored
  } catch { /* SSR */ }
  return 'en'
}

interface LocaleState {
  lang: Lang
  dir: Dir
  toggleLang: () => void
}

const initialLang = resolveInitialLang()
const initialDir: Dir = initialLang === 'he' ? 'rtl' : 'ltr'
if (typeof document !== 'undefined') {
  document.documentElement.dir = initialDir
  document.documentElement.lang = initialLang
}

export const useLocaleStore = create<LocaleState>((set) => ({
  lang: initialLang,
  dir: initialDir,
  toggleLang: () =>
    set((state) => {
      const next: Lang = state.lang === 'en' ? 'he' : 'en'
      const dir: Dir = next === 'he' ? 'rtl' : 'ltr'
      try { localStorage.setItem('lang', next) } catch { /* SSR */ }
      if (typeof document !== 'undefined') {
        document.documentElement.dir = dir
        document.documentElement.lang = next
      }
      return { lang: next, dir }
    }),
}))
