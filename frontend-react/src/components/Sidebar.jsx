import React from 'react'
import { getHydraStatusLabel, getHydraDotClass, getHydraAriaLabel } from '../utils/hydraStatus.js'
import { GitHubIcon } from './SourceIcons.jsx'

export default function Sidebar({ activeView, onNavigate, hydraStatus, onGoHome }) {
  const navItems = [
    {
      group: 'INVESTIGATE',
      items: [
        { id: 'ask', label: 'Ask', icon: <AskIcon /> },
        { id: 'trace', label: 'Trace', icon: <TraceIcon /> },
        { id: 'timeline', label: 'Timeline', icon: <TimelineIcon /> },
        { id: 'conflicts', label: 'Conflicts', icon: <ConflictsIcon /> },
      ],
    },
    {
      group: 'EXPLORE',
      items: [
        { id: 'graph', label: 'Graph Canvas', icon: <GraphCanvasIcon /> },
        { id: 'suggestions', label: 'Suggestions', icon: <SuggestionsIcon /> },
        { id: 'entities', label: 'Entities', icon: <EntityIcon /> },
      ],
    },
    {
      group: 'LEARN',
      items: [
        { id: 'why-hydra', label: 'How Veridex Works', icon: <ArchitectureIcon /> },
      ],
    },
    {
      group: 'SYSTEM',
      items: [
        { id: 'health', label: 'Graph Health', icon: <HealthIcon /> },
        {
          id: 'github',
          label: 'GitHub Repo ↗',
          icon: <GitHubIcon size={14} />,
          isExternal: true,
          href: 'https://github.com/toufiqfarhan0/deptrace',
        },
      ],
    },
  ]


  const isOnline = hydraStatus?.hydradb === 'ok'
  const isLoading = hydraStatus?.status === 'loading'

  return (
    <aside className="sidebar" role="navigation" aria-label="Main navigation">
      <div className="sidebar-wordmark">
        <button
          className="wordmark-name wordmark-home-btn"
          onClick={onGoHome}
          aria-label="Return to Veridex home"
          title="Back to home"
        >
          <VeridexLogoIcon />
          <span>VERIDEX</span>
        </button>
        <div className="wordmark-sub">INTELLIGENCE</div>
      </div>

      <nav className="sidebar-nav">
        {navItems.map((group) => (
          <div key={group.group} className="nav-group">
            <div className="nav-group-label">{group.group}</div>
            {group.items.map((item) =>
              item.isExternal ? (
                <a
                  key={item.id}
                  href={item.href}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="nav-item nav-item--external"
                  title="Open GitHub repository in new tab"
                >
                  <span className="nav-item-icon" aria-hidden="true">{item.icon}</span>
                  <span>{item.label}</span>
                </a>
              ) : (
                <button
                  key={item.id}
                  className={`nav-item ${activeView === item.id ? 'active' : ''}`}
                  onClick={() => onNavigate(item.id)}
                  aria-current={activeView === item.id ? 'page' : undefined}
                >
                  <span className="nav-item-icon" aria-hidden="true">{item.icon}</span>
                  {item.label}
                </button>
              )
            )}
          </div>
        ))}
      </nav>

      <div className="sidebar-footer">
        <a
          href="https://github.com/toufiqfarhan0/deptrace"
          target="_blank"
          rel="noopener noreferrer"
          className="sidebar-github-btn"
          title="View source code on GitHub"
          aria-label="View source code on GitHub"
        >
          <GitHubIcon size={14} />
          <span>GitHub Repo &#8599;</span>
        </a>
        <div
          className="status-line"
          role="status"
          aria-label={getHydraAriaLabel(hydraStatus)}
        >
          <span
            className={`status-dot ${getHydraDotClass(hydraStatus)}`}
            aria-hidden="true"
          />
          <span>
            {getHydraStatusLabel(hydraStatus, { format: 'sidebar' })}
          </span>
        </div>
      </div>
    </aside>
  )
}

function AskIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
      <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
    </svg>
  )
}

function TraceIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
      <circle cx="5" cy="5" r="2"/>
      <circle cx="19" cy="5" r="2"/>
      <circle cx="19" cy="19" r="2"/>
      <path d="M7 5h10M19 7v10"/>
    </svg>
  )
}

function SuggestionsIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
    </svg>
  )
}

function EntityIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
      <rect x="2" y="3" width="20" height="4" rx="1"/>
      <rect x="2" y="10" width="20" height="4" rx="1"/>
      <rect x="2" y="17" width="20" height="4" rx="1"/>
    </svg>
  )
}

function HealthIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
      <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
    </svg>
  )
}

function ArchitectureIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
      <circle cx="12" cy="12" r="3"/>
      <path d="M12 3v6M12 15v6M3 12h6M15 12h6"/>
    </svg>
  )
}

function TimelineIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <circle cx="12" cy="12" r="10"/>
      <polyline points="12 6 12 12 16 14"/>
    </svg>
  )
}

function ConflictsIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M16 3h5v5"/>
      <path d="M4 20L21 3"/>
      <path d="M21 16v5h-5"/>
      <path d="M15 15l6 6"/>
      <path d="M4 4l5 5"/>
    </svg>
  )
}

function GraphCanvasIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <circle cx="6" cy="6" r="3"/>
      <circle cx="18" cy="6" r="3"/>
      <circle cx="12" cy="18" r="3"/>
      <line x1="8.5" y1="7.5" x2="15.5" y2="7.5"/>
      <line x1="7.5" y1="8.5" x2="10.5" y2="15.5"/>
      <line x1="16.5" y1="8.5" x2="13.5" y2="15.5"/>
    </svg>
  )
}

function VeridexLogoIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--c-accent)" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" style={{ flexShrink: 0 }}>
      <circle cx="5" cy="5" r="2.5" fill="var(--c-accent)"/>
      <circle cx="19" cy="5" r="2.5" fill="var(--c-accent)"/>
      <circle cx="19" cy="19" r="2.5" fill="var(--c-accent)"/>
      <path d="M7.5 5h9M19 7.5v9"/>
    </svg>
  )
}



