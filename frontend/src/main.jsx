import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { Toaster } from 'react-hot-toast'
import './index.css'
import App from './App.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
    <Toaster
      position="top-right"
      toastOptions={{
        style: {
          background: '#272727',
          color: '#e5e5e5',
          border: '1px solid rgba(255,255,255,0.1)',
          borderRadius: '12px',
          fontSize: '13px',
        },
        success: {
          iconTheme: {
            primary: '#4ade80',
            secondary: '#272727',
          },
        },
        error: {
          iconTheme: {
            primary: '#f87171',
            secondary: '#272727',
          },
        },
      }}
    />
  </StrictMode>,
)
