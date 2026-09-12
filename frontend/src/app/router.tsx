import { createBrowserRouter, type RouteObject } from 'react-router-dom'
import { AppShell } from '../components/layout/AppShell'
import { ChartsPage } from '../pages/ChartsPage'
import { LiveDataPage } from '../pages/LiveDataPage'
import { OverviewPage } from '../pages/OverviewPage'
import { SystemPage } from '../pages/SystemPage'
import { ExperimentsPage } from '../pages/ExperimentsPage'
import { ExperimentDetailPage } from '../pages/ExperimentDetailPage'
import { ControlPage } from '../pages/ControlPage'

export const appRoutes: RouteObject[] = [
  {
    element: <AppShell />,
    children: [
      { index: true, element: <OverviewPage /> },
      { path: 'live', element: <LiveDataPage /> },
      { path: 'charts', element: <ChartsPage /> },
      { path: 'system', element: <SystemPage /> },
      { path: 'experiments', element: <ExperimentsPage /> },
      { path: 'experiments/:experimentId', element: <ExperimentDetailPage /> },
      { path: 'control', element: <ControlPage /> },
    ],
  },
]

export const appRouter = createBrowserRouter(appRoutes)
