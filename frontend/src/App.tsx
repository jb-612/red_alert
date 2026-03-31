import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Layout } from '@/components/layout/Layout'
import { DashboardPage } from '@/pages/DashboardPage'
import { ConflictsPage } from '@/pages/ConflictsPage'
import { useLocaleStore } from '@/store/locale'

export default function App() {
  useLocaleStore((s) => s.dir) // subscribe to trigger re-render on locale change

  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/conflicts" element={<ConflictsPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
