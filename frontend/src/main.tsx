import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { App } from './app/App'
import { registerPwa } from './pwa/registerPwa'
import './styles/index.css'

registerPwa()

const rootElement = document.getElementById('root')

if (!rootElement) {
  throw new Error('BioVolt root element is missing')
}

createRoot(rootElement).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
