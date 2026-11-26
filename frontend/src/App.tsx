
import { useEffect, useState } from 'react'
import { getHealth } from './services/healthService'
import type { HealthResponse } from './types/health'
import './App.css'

function App() {
  const [health, setHealth] = useState<HealthResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const controller = new AbortController()

    getHealth(controller.signal)
      .then(setHealth)
      .catch((err: unknown) => {
        if (!controller.signal.aborted) {
          setError(
            err instanceof Error ? err.message : 'Unknown error',
          )
        }
      })

    return () => controller.abort()
  }, [])

  return (
    <main>
      <h1>CodePulse</h1>
      <p>AI-powered Engineering Intelligence Platform</p>

      <section>
        <h2>System Status</h2>

        {error ? (
          <p>Backend unavailable: {error}</p>
        ) : health ? (
          <>
            <p>Service: {health.service}</p>
            <p>Status: {health.status}</p>
            <p>Version: {health.version}</p>
          </>
        ) : (
          <p>Connecting to backend...</p>
        )}
      </section>
    </main>
  )
}

export default App
