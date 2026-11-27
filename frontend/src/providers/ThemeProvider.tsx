
import { useEffect, useState } from 'react'
import type { ReactNode } from 'react'

import { ThemeContext } from './theme-context'

import type {
  Appearance,
  Palette,
  ThemePreferences,
} from './theme-context'

const STORAGE_KEY = 'eip.appearance.v1'

const DEFAULT_PREFERENCES: ThemePreferences = {
  palette: 'wine',
  appearance: 'day',
}

const PALETTES: Palette[] = [
  'wine',
  'emerald',
  'charcoal',
  'plum',
]

const APPEARANCES: Appearance[] = [
  'day',
  'evening',
  'night',
  'system',
]

function loadPreferences(): ThemePreferences {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)

    if (!raw) return DEFAULT_PREFERENCES

    const saved = JSON.parse(raw) as Partial<ThemePreferences>

    return {
      palette: PALETTES.includes(saved.palette as Palette)
        ? saved.palette as Palette
        : DEFAULT_PREFERENCES.palette,

      appearance: APPEARANCES.includes(
        saved.appearance as Appearance,
      )
        ? saved.appearance as Appearance
        : DEFAULT_PREFERENCES.appearance,
    }
  } catch {
    return DEFAULT_PREFERENCES
  }
}

export function ThemeProvider({
  children,
}: {
  children: ReactNode
}) {
  const [preferences, setPreferences] =
    useState<ThemePreferences>(loadPreferences)

  useEffect(() => {
    const media = window.matchMedia(
      '(prefers-color-scheme: dark)',
    )

    function applyTheme() {
      const mode = preferences.appearance === 'system'
        ? media.matches ? 'night' : 'day'
        : preferences.appearance

      document.documentElement.dataset.palette =
        preferences.palette

      document.documentElement.dataset.mode = mode

      document.documentElement.style.colorScheme =
        mode === 'night' ? 'dark' : 'light'
    }

    applyTheme()

    media.addEventListener('change', applyTheme)

    try {
      localStorage.setItem(
        STORAGE_KEY,
        JSON.stringify(preferences),
      )
    } catch {
      // Preferences remain usable without browser storage.
    }

    return () => {
      media.removeEventListener('change', applyTheme)
    }
  }, [preferences])

  function setPalette(palette: Palette) {
    setPreferences(previous => ({
      ...previous,
      palette,
    }))
  }

  function setAppearance(appearance: Appearance) {
    setPreferences(previous => ({
      ...previous,
      appearance,
    }))
  }

  return (
    <ThemeContext.Provider
      value={{
        ...preferences,
        setPalette,
        setAppearance,
      }}
    >
      {children}
    </ThemeContext.Provider>
  )
}
