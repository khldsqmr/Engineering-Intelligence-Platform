import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'

import { QueryClientProvider } from '@tanstack/react-query'

import { ThemeProvider } from './providers/ThemeProvider'
import {
  ReportingPeriodProvider,
} from './providers/ReportingPeriodProvider'

import { queryClient } from './providers/queryClient'

import './index.css'
import App from './App.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <ReportingPeriodProvider>
          <App />
        </ReportingPeriodProvider>
      </ThemeProvider>
    </QueryClientProvider>
  </StrictMode>,
)
