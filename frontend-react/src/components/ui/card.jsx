import React from 'react'

export function Card({ className = '', children, ...props }) {
  return <div className={`shadcn-card ${className}`.trim()} {...props}>{children}</div>
}

export function CardHeader({ className = '', children, ...props }) {
  return <div className={`shadcn-card-header ${className}`.trim()} {...props}>{children}</div>
}

export function CardTitle({ className = '', children, ...props }) {
  return <h3 className={`shadcn-card-title ${className}`.trim()} {...props}>{children}</h3>
}

export function CardDescription({ className = '', children, ...props }) {
  return <p className={`shadcn-card-description ${className}`.trim()} {...props}>{children}</p>
}

export function CardContent({ className = '', children, ...props }) {
  return <div className={`shadcn-card-content ${className}`.trim()} {...props}>{children}</div>
}

export function CardFooter({ className = '', children, ...props }) {
  return <div className={`shadcn-card-footer ${className}`.trim()} {...props}>{children}</div>
}
