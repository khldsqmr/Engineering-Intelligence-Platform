import { useEffect, useId, useRef } from 'react'
import type { ReactNode } from 'react'

import { X } from 'lucide-react'

interface DetailDrawerProps {
  open: boolean
  onClose: () => void
  title: string
  subtitle?: string
  children: ReactNode
}

export function DetailDrawer({
  open,
  onClose,
  title,
  subtitle,
  children,
}: DetailDrawerProps) {
  const dialogRef = useRef<HTMLDialogElement>(null)
  const titleId = useId()

  useEffect(() => {
    const dialog = dialogRef.current

    if (!dialog) return

    if (open && !dialog.open) {
      dialog.showModal()
    }

    if (!open && dialog.open) {
      dialog.close()
    }
  }, [open])

  return (
    <dialog
      ref={dialogRef}
      className="detail-drawer"
      aria-labelledby={titleId}
      onClose={onClose}
    >
      <header className="drawer-header">

        <div>
          {subtitle && (
            <span className="drawer-subtitle">
              {subtitle}
            </span>
          )}

          <h2 id={titleId}>{title}</h2>
        </div>

        <button
          type="button"
          className="icon-button"
          aria-label="Close details"
          onClick={onClose}
        >
          <X size={20} />
        </button>

      </header>

      <div className="drawer-content">
        {children}
      </div>
    </dialog>
  )
}
