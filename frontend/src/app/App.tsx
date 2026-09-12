import { RouterProvider } from 'react-router-dom'
import { appRouter } from './router'
import { AppSurface } from '../components/layout/AppSurface'

export function App() {
  return (
    <AppSurface>
      <RouterProvider router={appRouter} />
    </AppSurface>
  )
}
