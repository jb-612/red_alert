import { create } from 'zustand'

function resolveInitialTheme(): boolean {
  const stored = localStorage.getItem('theme')
  if (stored) return stored === 'dark'
  return window.matchMedia('(prefers-color-scheme: dark)').matches
}

interface ThemeState {
  dark: boolean
  toggle: () => void
}

const initialDark = resolveInitialTheme()
document.documentElement.classList.toggle('dark', initialDark)

export const useThemeStore = create<ThemeState>((set) => ({
  dark: initialDark,
  toggle: () =>
    set((state) => {
      const next = !state.dark
      localStorage.setItem('theme', next ? 'dark' : 'light')
      document.documentElement.classList.toggle('dark', next)
      return { dark: next }
    }),
}))
