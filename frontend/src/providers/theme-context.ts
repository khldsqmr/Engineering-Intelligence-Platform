
import { createContext, useContext } from 'react'

export type Palette =
  | 'wine'
  | 'emerald'
  | 'charcoal'
  | 'plum'

export type Appearance =
  | 'day'
  | 'evening'
  | 'night'
  | 'system'

export interface ThemePreferences {
  palette: Palette
  appearance: Appearance
}

interface ThemeContextValue extends ThemePreferences {
  setPalette: (palette: Palette) => void
  setAppearance: (appearance: Appearance) => void
}

export const ThemeContext =
  createContext<ThemeContextValue | undefined>(
    undefined,
  )

export function useTheme() {
  const context = useContext(ThemeContext)

  if (!context) {
    throw new Error(
      'useTheme must be used within ThemeProvider',
    )
  }

  return context
}
