import { createBrowserRouter, type RouteObject } from 'react-router-dom'
import { AppShell } from '../components/layout/AppShell'
import { ChartsPage } from '../pages/ChartsPage'
import { LiveDataPage } from '../pages/LiveDataPage'
import { OverviewPage } from '../pages/OverviewPage'
import { SystemPage } from '../pages/SystemPage'

export const appRoutes: RouteObject[] = [
  {
    element: <AppShell />,
    children: [
      { index: true, element: <OverviewPage /> },
      { path: 'live', element: <LiveDataPage /> },
      { path: 'charts', element: <ChartsPage /> },
      { path: 'system', element: <SystemPage /> },
    ],
  },
]

export const appRouter = createBrowserRouter(appRoutes)
