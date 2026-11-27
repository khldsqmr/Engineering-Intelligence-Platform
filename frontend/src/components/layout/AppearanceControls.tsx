
import {
  Monitor,
  Moon,
  Palette as PaletteIcon,
  Sun,
  Sunset,
} from 'lucide-react'

import { useTheme } from '../../providers/theme-context'

import type {
  Appearance,
  Palette,
} from '../../providers/theme-context'

import './AppearanceControls.css'

const appearanceIcons = {
  day: Sun,
  evening: Sunset,
  night: Moon,
  system: Monitor,
}

export function AppearanceControls() {
  const {
    palette,
    appearance,
    setPalette,
    setAppearance,
  } = useTheme()

  const AppearanceIcon = appearanceIcons[appearance]

  return (
    <div className="appearance-controls">

      <label
        className="appearance-control"
        title="Change color palette"
      >
        <PaletteIcon size={19} aria-hidden="true" />

        <select
          aria-label="Color palette"
          value={palette}
          onChange={event =>
            setPalette(event.target.value as Palette)
          }
        >
          <option value="wine">Wine & Gold</option>
          <option value="emerald">Emerald & Champagne</option>
          <option value="charcoal">Charcoal & Copper</option>
          <option value="plum">Plum & Rose Gold</option>
        </select>
      </label>

      <label
        className="appearance-control"
        title="Change appearance"
      >
        <AppearanceIcon size={19} aria-hidden="true" />

        <select
          aria-label="Appearance mode"
          value={appearance}
          onChange={event =>
            setAppearance(event.target.value as Appearance)
          }
        >
          <option value="day">Day</option>
          <option value="evening">Evening</option>
          <option value="night">Night</option>
          <option value="system">System</option>
        </select>
      </label>

    </div>
  )
}
