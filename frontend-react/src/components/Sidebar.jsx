import React from 'react'

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
        { id: 'entities', label: 'Entities', icon: <EntityIcon /> },
      ],
    },
    {
      group: 'SYSTEM',
      items: [
        { id: 'why-hydra', label: 'Why HydraDB?', icon: <ArchitectureIcon /> },
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
        <div className="status-line">
          <span
            className={`status-dot ${isLoading ? 'loading' : isOnline ? 'ok' : 'err'}`}
            aria-hidden="true"
          />
          <span>
            {isLoading
              ? 'Checking HydraDB...'
              : isOnline
              ? 'HydraDB Online'
              : 'HydraDB Offline'}
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

