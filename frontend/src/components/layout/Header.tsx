import { NavLink } from 'react-router-dom'
import { useThemeStore } from '@/store/theme'
import { useLocaleStore } from '@/store/locale'
import { useLabels } from '@/lib/labels'
import { Button } from '@/components/ui/button'

export function Header() {
  const { dark, toggle } = useThemeStore()
  const { lang, toggleLang } = useLocaleStore()
  const labels = useLabels()

  return (
    <header className="flex items-center justify-between border-b border-border px-6 py-3">
      <div className="flex items-center gap-6">
        <div className="flex items-center gap-3">
          <div className="h-8 w-8 rounded-full bg-red-600 flex items-center justify-center">
            <span className="text-white text-sm font-bold">!</span>
          </div>
          <h1 className="text-xl font-semibold tracking-tight text-foreground">
            {labels.appTitle}
          </h1>
        </div>
        <nav className="flex items-center gap-1">
          <NavLink
            to="/dashboard"
            className={({ isActive }) =>
              `px-3 py-1.5 text-sm font-medium transition-colors ${
                isActive
                  ? 'text-foreground border-b-2 border-red-500'
                  : 'text-muted-foreground hover:text-foreground'
              }`
            }
          >
            Red Alert
          </NavLink>
          <NavLink
            to="/conflicts"
            className={({ isActive }) =>
              `px-3 py-1.5 text-sm font-medium transition-colors ${
                isActive
                  ? 'text-foreground border-b-2 border-red-500'
                  : 'text-muted-foreground hover:text-foreground'
              }`
            }
          >
            {labels.conflicts}
          </NavLink>
        </nav>
      </div>
      <div className="flex items-center gap-2">
        <Button variant="ghost" size="sm" onClick={toggleLang} className="text-muted-foreground">
          {lang === 'en' ? '\u05E2\u05D1' : 'EN'}
        </Button>
        <Button variant="ghost" size="sm" onClick={toggle} className="text-muted-foreground">
          {dark ? 'Light' : 'Dark'}
        </Button>
      </div>
    </header>
  )
}
