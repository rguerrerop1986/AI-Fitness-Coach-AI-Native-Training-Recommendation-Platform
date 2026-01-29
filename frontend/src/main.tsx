import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import './index.css'
import './i18n'
import App from './App.tsx'
import ErrorBoundary from './components/ErrorBoundary'

// Ensure root element exists
const rootElement = document.getElementById('root')
if (!rootElement) {
  throw new Error('Root element not found')
}

ReactDOM.createRoot(rootElement).render(
  <React.StrictMode>
    <ErrorBoundary>
      <BrowserRouter>
        <App />
        <Toaster 
          position="top-right"
          toastOptions={{
            duration: 4000,
            style: {
              background: '#363636',
              color: '#fff',
            },
            className: 'dark:bg-gray-800 dark:text-gray-100',
          }}
        />
      </BrowserRouter>
    </ErrorBoundary>
  </React.StrictMode>,
)
