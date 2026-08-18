import React from 'react'
import { getHydraStatusLabel, getHydraDotClass, getHydraAriaLabel } from '../utils/hydraStatus.js'

export default function Sidebar({ activeView, onNavigate, hydraStatus, onGoHome }) {
  const navItems = [
    {
      group: 'INVESTIGATE',
      items: [
        { id: 'ask', label: 'Ask', icon: <AskIcon /> },
        { id: 'trace', label: 'Trace', icon: <TraceIcon /> },
      ],
    },
    {
      group: 'EXPLORE',
      items: [
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
          VERIDEX
          <span className="wordmark-tag">TRACK 1</span>
        </button>
        <div className="wordmark-sub">Evidence-first dependency intelligence</div>
      </div>

      <nav className="sidebar-nav">
        {navItems.map((group) => (
          <div key={group.group} className="nav-group">
            <div className="nav-group-label">{group.group}</div>
            {group.items.map((item) => (
              <button
                key={item.id}
                className={`nav-item ${activeView === item.id ? 'active' : ''}`}
                onClick={() => onNavigate(item.id)}
                aria-current={activeView === item.id ? 'page' : undefined}
              >
                <span className="nav-item-icon" aria-hidden="true">{item.icon}</span>
                {item.label}
              </button>
            ))}
          </div>
        ))}
      </nav>

      <div className="sidebar-footer">
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

