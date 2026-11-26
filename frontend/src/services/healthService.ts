//We are separating API communication from the UI components.

//This keeps React components focused on presentation while our service layer handles HTTP requests and errors.

//We are using the browser's built-in fetch() instead of installing Axios because our current requirements do not justify an additional dependency.

import type { HealthResponse } from '../types/health'

export async function getHealth(
  signal?: AbortSignal,
): Promise<HealthResponse> {
  const response = await fetch('/api/health', { signal })

  if (!response.ok) {
    throw new Error(`Health check failed: ${response.status}`)
  }

  return response.json()
}