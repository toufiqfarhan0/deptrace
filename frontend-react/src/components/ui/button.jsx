import React from 'react'

export function Button({
  className = '',
  variant = 'default',
  size = 'default',
  children,
  ...props
}) {
  const variantClass = `shadcn-btn shadcn-btn--${variant} shadcn-btn--${size} ${className}`
  return (
    <button className={variantClass.trim()} {...props}>
      {children}
    </button>
  )
}
