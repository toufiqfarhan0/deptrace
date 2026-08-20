import React from 'react'

export function Badge({
  className = '',
  variant = 'default',
  children,
  ...props
}) {
  return (
    <span className={`shadcn-badge shadcn-badge--${variant} ${className}`.trim()} {...props}>
      {children}
    </span>
  )
}
