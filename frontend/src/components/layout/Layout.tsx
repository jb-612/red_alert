import { Outlet } from 'react-router-dom'
import { Header } from './Header'

export function Layout() {
  return (
    <div className="flex h-screen flex-col bg-background text-foreground">
      <Header />
      <Outlet />
    </div>
  )
}
