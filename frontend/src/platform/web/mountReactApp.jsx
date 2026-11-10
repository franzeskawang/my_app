// Web-only bootstrap: this is the only frontend module that accesses the document.
import React from 'react'
import { createRoot } from 'react-dom/client'
import App from '../../App.jsx'
import '../../styles.css'

export function mountReactApp() {
  const rootElement = document.getElementById('root')
  if (!rootElement) throw new Error('Missing #root mount element')
  createRoot(rootElement).render(<React.StrictMode><App /></React.StrictMode>)
}
