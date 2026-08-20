import React from 'react'

/**
 * Official application icons for multi-source knowledge integration
 * (Slack, Linear, GitHub, PagerDuty, System/HydraDB).
 */

export function SlackIcon({ size = 16, className = '', style = {} }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      className={`source-app-icon icon-slack ${className}`}
      style={{ flexShrink: 0, display: 'inline-block', verticalAlign: 'middle', ...style }}
      aria-hidden="true"
    >
      <path
        d="M5.042 15.165a2.528 2.528 0 0 1-2.52 2.523A2.528 2.528 0 0 1 0 15.165a2.527 2.527 0 0 1 2.522-2.52h2.52v2.52zM6.313 15.165a2.527 2.527 0 0 1 2.521-2.52 2.527 2.527 0 0 1 2.521 2.52v6.313A2.528 2.528 0 0 1 8.834 24a2.528 2.528 0 0 1-2.521-2.522v-6.313z"
        fill="#ECB22E"
      />
      <path
        d="M8.834 5.042a2.528 2.528 0 0 1-2.521-2.52A2.528 2.528 0 0 1 8.834 0a2.528 2.528 0 0 1 2.521 2.522v2.52H8.834zM8.834 6.313a2.528 2.528 0 0 1 2.521 2.521 2.528 2.528 0 0 1-2.521 2.521H2.522A2.528 2.528 0 0 1 0 8.834a2.528 2.528 0 0 1 2.522-2.521h6.312z"
        fill="#36C5F0"
      />
      <path
        d="M18.956 8.834a2.528 2.528 0 0 1 2.522-2.521A2.528 2.528 0 0 1 24 8.834a2.528 2.528 0 0 1-2.522 2.521h-2.522V8.834zM17.688 8.834a2.528 2.528 0 0 1-2.523 2.521 2.527 2.527 0 0 1-2.52-2.521V2.522A2.527 2.527 0 0 1 15.165 0a2.528 2.528 0 0 1 2.523 2.522v6.312z"
        fill="#2EB67D"
      />
      <path
        d="M15.165 18.956a2.528 2.528 0 0 1 2.523 2.522A2.528 2.528 0 0 1 15.165 24a2.527 2.527 0 0 1-2.52-2.522v-2.522h2.52zM15.165 17.688a2.527 2.527 0 0 1-2.52-2.523 2.526 2.526 0 0 1 2.52-2.52h6.313A2.527 2.527 0 0 1 24 15.165a2.528 2.528 0 0 1-2.522 2.523h-6.313z"
        fill="#E01E5A"
      />
    </svg>
  )
}

export function LinearIcon({ size = 16, className = '', style = {} }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 100 100"
      fill="none"
      className={`source-app-icon icon-linear ${className}`}
      style={{ flexShrink: 0, display: 'inline-block', verticalAlign: 'middle', ...style }}
      aria-hidden="true"
    >
      <path
        d="M8.8 62.4L62.4 8.8C58.5 6.3 54.4 4.8 50 4.8 25 4.8 4.8 25 4.8 50c0 4.4 1.5 8.5 4 12.4zm4.4 10.8c5.4 6.8 12.6 11.8 20.8 14.2L87.4 34c-2.4-8.2-7.4-15.4-14.2-20.8L13.2 73.2zm24.4 22c4 .8 8.1 1.2 12.4 1.2 25 0 45.2-20.2 45.2-45.2 0-4.3-.4-8.4-1.2-12.4L37.6 95.2z"
        fill="#6366F1"
      />
    </svg>
  )
}

export function GitHubIcon({ size = 16, className = '', color = 'currentColor', style = {} }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill={color}
      className={`source-app-icon icon-github ${className}`}
      style={{ flexShrink: 0, display: 'inline-block', verticalAlign: 'middle', ...style }}
      aria-hidden="true"
    >
      <path
        fillRule="evenodd"
        clipRule="evenodd"
        d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.53 1.032 1.53 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z"
      />
    </svg>
  )
}

export function PagerDutyIcon({ size = 16, className = '', color = '#10B981', style = {} }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      className={`source-app-icon icon-pagerduty ${className}`}
      style={{ flexShrink: 0, display: 'inline-block', verticalAlign: 'middle', ...style }}
      aria-hidden="true"
    >
      <circle cx="12" cy="12" r="10" stroke={color} strokeWidth="2.2" />
      <path d="M9 8h4.5a2.5 2.5 0 0 1 0 5H9V8zm0 5v4" stroke={color} strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

export function JiraIcon({ size = 16, className = '', style = {} }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      className={`source-app-icon icon-jira ${className}`}
      style={{ flexShrink: 0, display: 'inline-block', verticalAlign: 'middle', ...style }}
      aria-hidden="true"
    >
      <path
        d="M11.53 2c0 5.258-4.28 9.52-9.53 9.52V2h9.53z"
        fill="#0052CC"
      />
      <path
        d="M11.53 12.48c0 5.258-4.28 9.52-9.53 9.52v-9.52h9.53z"
        fill="#2684FF"
      />
      <path
        d="M22 12.48c0 5.258-4.28 9.52-9.53 9.52v-9.52H22z"
        fill="#0052CC"
      />
    </svg>
  )
}

export function ConfluenceIcon({ size = 16, className = '', style = {} }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      className={`source-app-icon icon-confluence ${className}`}
      style={{ flexShrink: 0, display: 'inline-block', verticalAlign: 'middle', ...style }}
      aria-hidden="true"
    >
      <path
        d="M3.24 18.06c-.84-.84-.96-2.16-.27-3.12l4.89-6.84c.69-.96 2.01-1.2 2.97-.51l2.4 1.71c.96.69 1.2 2.01.51 2.97l-4.89 6.84c-.69.96-2.01 1.2-2.97.51l-2.64-1.56z"
        fill="#172B4D"
      />
      <path
        d="M20.76 5.94c.84.84.96 2.16.27 3.12l-4.89 6.84c-.69.96-2.01 1.2-2.97.51l-2.4-1.71c-.96-.69-1.2-2.01-.51-2.97l4.89-6.84c.69-.96 2.01-1.2 2.97-.51l2.64 1.56z"
        fill="#0052CC"
      />
    </svg>
  )
}

/**
 * Universal SourceIcon resolver
 */
export function SourceIcon({ source, size = 14, className = '', style = {} }) {
  const norm = (source || '').toLowerCase().trim()
  if (norm.includes('slack')) return <SlackIcon size={size} className={className} style={style} />
  if (norm.includes('linear')) return <LinearIcon size={size} className={className} style={style} />
  if (norm.includes('github') || norm.startsWith('pr-')) return <GitHubIcon size={size} className={className} style={style} />
  if (norm.includes('jira')) return <JiraIcon size={size} className={className} style={style} />
  if (norm.includes('confluence') || norm.startsWith('rfc-') || norm.startsWith('adr-')) return <ConfluenceIcon size={size} className={className} style={style} />
  if (norm.includes('pagerduty')) return <PagerDutyIcon size={size} className={className} style={style} />

  // Generic System / Graph Node
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={`source-app-icon icon-system ${className}`}
      style={{ flexShrink: 0, display: 'inline-block', verticalAlign: 'middle', ...style }}
      aria-hidden="true"
    >
      <circle cx="12" cy="12" r="8" />
      <path d="M12 8v4l2 2" />
    </svg>
  )
}
