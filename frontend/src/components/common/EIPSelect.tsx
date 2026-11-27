import * as Select from '@radix-ui/react-select'
import { Check, ChevronDown, ChevronUp } from 'lucide-react'

import './EIPSelect.css'

export interface SelectOption {
  value: string
  label: string
  disabled?: boolean
}

export interface SelectGroup {
  label?: string
  options: SelectOption[]
}

interface EIPSelectProps {
  id?: string
  ariaLabel?: string
  value: string
  onChange: (value: string) => void
  groups: SelectGroup[]
  placeholder?: string
  disabled?: boolean
  className?: string
}

export function EIPSelect({
  id,
  ariaLabel,
  value,
  onChange,
  groups,
  placeholder = 'Select an option',
  disabled = false,
  className = '',
}: EIPSelectProps) {
  return (
    <Select.Root
      value={value}
      onValueChange={onChange}
      disabled={disabled}
    >
      <Select.Trigger
        id={id}
        aria-label={ariaLabel}
        className={`eip-select-trigger ${className}`}
      >
        <Select.Value placeholder={placeholder} />

        <Select.Icon asChild>
          <ChevronDown
            size={15}
            className="eip-select-chevron"
          />
        </Select.Icon>
      </Select.Trigger>

      <Select.Portal>
        <Select.Content
          className="eip-select-content"
          position="popper"
          side="bottom"
          align="start"
          sideOffset={4}
          collisionPadding={12}
          avoidCollisions
        >
          <Select.ScrollUpButton className="eip-select-scroll">
            <ChevronUp size={14} />
          </Select.ScrollUpButton>

          <Select.Viewport className="eip-select-viewport">
            {groups.map((group, index) => (
              <Select.Group
                key={group.label ?? index}
                className="eip-select-group"
              >
                {group.label && (
                  <Select.Label className="eip-select-label">
                    {group.label}
                  </Select.Label>
                )}

                {group.options.map(option => (
                  <Select.Item
                    key={option.value}
                    value={option.value}
                    disabled={option.disabled}
                    className="eip-select-item"
                  >
                    <Select.ItemText>
                      {option.label}
                    </Select.ItemText>

                    <Select.ItemIndicator
                      className="eip-select-indicator"
                    >
                      <Check size={14} />
                    </Select.ItemIndicator>
                  </Select.Item>
                ))}
              </Select.Group>
            ))}
          </Select.Viewport>

          <Select.ScrollDownButton className="eip-select-scroll">
            <ChevronDown size={14} />
          </Select.ScrollDownButton>
        </Select.Content>
      </Select.Portal>
    </Select.Root>
  )
}
