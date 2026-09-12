import { RouterProvider } from 'react-router-dom'
import { appRouter } from './router'
import { AppSurface } from '../components/layout/AppSurface'
import { useDashboardSocket } from '../hooks/useDashboardSocket'
import { useSystemStatus } from '../hooks/useSystemStatus'

export function App() {
  useDashboardSocket()
  useSystemStatus()

  return (
    <AppSurface>
      <RouterProvider router={appRouter} />
    </AppSurface>
  )
}
