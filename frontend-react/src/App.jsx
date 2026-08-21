import React, { useState, useEffect, useCallback } from 'react'
import LandingPage from './components/LandingPage.jsx'
import Sidebar from './components/Sidebar.jsx'
import InvestigationView from './components/InvestigationView.jsx'
import TraceView from './components/TraceView.jsx'
import TimelinePlayer from './components/TimelinePlayer.jsx'
import ConflictResolverView from './components/ConflictResolverView.jsx'
import GraphExplorerView from './components/GraphExplorerView.jsx'
import SuggestionsView from './components/SuggestionsView.jsx'
import EntityExplorer from './components/EntityExplorer.jsx'
import GraphHealth from './components/GraphHealth.jsx'
import WhyHydraDB from './components/WhyHydraDB.jsx'
import ThemeToggle from './components/ThemeToggle.jsx'
import { getHydraStatusLabel, getHydraDotClass, getHydraAriaLabel } from './utils/hydraStatus.js'
import { useQuota } from './utils/quotaManager.js'

export default function App() {
  const quota = useQuota()
  // Theme System: default to light mode, toggleable to dark mode
  const [theme, setTheme] = useState(() => {
    try {
      const saved = localStorage.getItem('veridex-theme')
      if (saved === 'light' || saved === 'dark') return saved
    } catch {
      // Ignore localStorage access failures
    }
    return 'light'
  })

  useEffect(() => {
    try {
      document.documentElement.setAttribute('data-theme', theme)
      localStorage.setItem('veridex-theme', theme)
    } catch {
      // Ignore storage errors
    }
  }, [theme])

  const toggleTheme = useCallback(() => {
    setTheme((prev) => (prev === 'dark' ? 'light' : 'dark'))
  }, [])

  // 'landing' shows the product entry page; any console view key shows the console
  const [view, setView] = useState('landing')
  const [activeView, setActiveView] = useState('ask')
  const [hydraStatus, setHydraStatus] = useState({ status: 'loading', hydradb: '' })
  const [askQuery, setAskQuery] = useState('')
  const [traceEntity, setTraceEntity] = useState('')
  const [timelineEntity, setTimelineEntity] = useState('INC-2026')
  const [sessionKey, setSessionKey] = useState(0)

  const checkHealth = useCallback(async () => {
    try {
      const res = await fetch('/api/health')
      const data = await res.json()
      setHydraStatus(data)
    } catch {
      setHydraStatus({ status: 'error', hydradb: 'unreachable' })
    }
  }, [])

  useEffect(() => {
    checkHealth()
    const interval = setInterval(checkHealth, 30000)
    return () => clearInterval(interval)
  }, [checkHealth])

  const navigateToAsk = useCallback((query = '') => {
    if (query) setAskQuery(query)
    setActiveView('ask')
    setView('console')
  }, [])

  const navigateToTrace = useCallback((entity = '') => {
    if (entity) setTraceEntity(entity)
    setActiveView('trace')
    setView('console')
  }, [])

  const navigateToTimeline = useCallback((entity = '') => {
    if (entity) setTimelineEntity(entity)
    setActiveView('timeline')
    setView('console')
  }, [])

  const navigateToConflicts = useCallback(() => {
    setActiveView('conflicts')
    setView('console')
  }, [])

  // Entry point from landing page CTAs — switches to console view with optional query
  const enterConsole = useCallback((consoleView = 'ask', initialQuery = '') => {
    if (initialQuery) {
      if (consoleView === 'trace') {
        setTraceEntity(initialQuery)
      } else if (consoleView === 'timeline') {
        setTimelineEntity(initialQuery)
      } else {
        setAskQuery(initialQuery)
      }
    }
    setActiveView(consoleView)
    setView('console')
  }, [])

  const navigateToWhyHydra = useCallback(() => {
    setActiveView('why-hydra')
    setView('console')
  }, [])

  // Landing page navigation: resets console outputs and search bars for a fresh session
  const handleGoLanding = useCallback(() => {
    setAskQuery('')
    setTraceEntity('')
    setTimelineEntity('INC-2026')
    setSessionKey((prev) => prev + 1)
    setView('landing')
  }, [])

  const getBreadcrumb = () => {
    switch (activeView) {
      case 'ask': return 'Investigate / Ask'
      case 'trace': return 'Investigate / Trace'
      case 'timeline': return 'Investigate / Incident Timeline'
      case 'conflicts': return 'Investigate / Conflict Arbiter'
      case 'graph': return 'Explore / Graph Canvas'
      case 'suggestions': return 'Explore / Suggestions'
      case 'entities': return 'Explore / Entities'
      case 'why-hydra': return 'Learn / How Veridex Works'
      case 'health': return 'System / Graph Health'
      default: return 'Investigate'
    }
  }

  if (view === 'landing') {
    return (
      <LandingPage
        onEnterConsole={enterConsole}
        onNavigateToWhyHydra={navigateToWhyHydra}
        hydraStatus={hydraStatus}
        theme={theme}
        onToggleTheme={toggleTheme}
      />
    )
  }

  return (
    <div className="shell">
      <Sidebar
        activeView={activeView}
        onNavigate={(v) => { setActiveView(v); setView('console') }}
        hydraStatus={hydraStatus}
        onGoHome={handleGoLanding}
      />
      <div className="workspace">
        <header className="workspace-header">
          <nav className="breadcrumb" aria-label="Current location">
            <button
              className="breadcrumb-home"
              onClick={handleGoLanding}
              aria-label="Return to Veridex home"
            >
              VERIDEX
            </button>
            <span className="breadcrumb-sep">/</span>
            <span className="breadcrumb-active">{getBreadcrumb()}</span>
          </nav>
          <div className="header-actions">
            <div className={`quota-header-badge ${quota.isExceeded ? 'exceeded' : ''}`} title={`Demo Usage Quota: ${quota.remaining}/${quota.maxQuota}`}>
              <span>Quota:</span>
              <strong>{quota.remaining} / {quota.maxQuota}</strong>
            </div>
            <ThemeToggle theme={theme} onToggleTheme={toggleTheme} />
            <div
              className="header-status"
              role="status"
              aria-label={getHydraAriaLabel(hydraStatus)}
            >
              <span
                className={`status-dot ${getHydraDotClass(hydraStatus)}`}
                aria-hidden="true"
              />
              <span>
                {getHydraStatusLabel(hydraStatus, { format: 'header' })}
              </span>
            </div>
          </div>
        </header>

        <main className="workspace-body" id="main-content" role="main">
          {/* Keep Ask, Trace, and Timeline views mounted in DOM so execution state persists during tab navigation */}
          <div style={{ display: activeView === 'ask' ? 'block' : 'none' }}>
            <InvestigationView
              key={`ask-${sessionKey}`}
              initialQuery={askQuery}
              onQueryChange={setAskQuery}
              onNavigateToTrace={navigateToTrace}
              onNavigateToTimeline={navigateToTimeline}
              isActive={activeView === 'ask'}
            />
          </div>
          <div style={{ display: activeView === 'trace' ? 'block' : 'none' }}>
            <TraceView
              key={`trace-${sessionKey}`}
              initialEntity={traceEntity}
              onEntityChange={setTraceEntity}
              onNavigateToAsk={navigateToAsk}
              onNavigateToTimeline={navigateToTimeline}
              isActive={activeView === 'trace'}
            />
          </div>
          <div style={{ display: activeView === 'timeline' ? 'block' : 'none' }}>
            <TimelinePlayer
              key={`timeline-${sessionKey}`}
              initialEntity={timelineEntity}
              onNavigateToAsk={navigateToAsk}
              onNavigateToTrace={navigateToTrace}
              isActive={activeView === 'timeline'}
            />
          </div>
          {activeView === 'conflicts' && (
            <ConflictResolverView
              onNavigateToAsk={navigateToAsk}
              onNavigateToTrace={navigateToTrace}
            />
          )}
          {activeView === 'graph' && (
            <GraphExplorerView
              onNavigateToAsk={navigateToAsk}
              onNavigateToTrace={navigateToTrace}
              onNavigateToTimeline={navigateToTimeline}
            />
          )}
          {activeView === 'suggestions' && (
            <SuggestionsView
              onSelectQuery={navigateToAsk}
              onSelectTrace={navigateToTrace}
            />
          )}
          {activeView === 'entities' && (
            <EntityExplorer
              key={`entities-${sessionKey}`}
              onTraceEntity={navigateToTrace}
              onAskEntity={navigateToAsk}
            />
          )}
          {activeView === 'why-hydra' && (
            <WhyHydraDB
              onNavigateToAsk={navigateToAsk}
              onNavigateToTrace={navigateToTrace}
              onNavigateToTimeline={navigateToTimeline}
              onNavigateToConflicts={() => setActiveView('conflicts')}
              onNavigateToGraph={() => setActiveView('graph')}
            />
          )}
          {activeView === 'health' && <GraphHealth hydraStatus={hydraStatus} />}
        </main>
      </div>
    </div>
  )
}


