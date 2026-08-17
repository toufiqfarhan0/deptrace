import React, { useState, useEffect, useCallback } from 'react'
import LandingPage from './components/LandingPage.jsx'
import Sidebar from './components/Sidebar.jsx'
import InvestigationView from './components/InvestigationView.jsx'
import TraceView from './components/TraceView.jsx'
import EntityExplorer from './components/EntityExplorer.jsx'
import GraphHealth from './components/GraphHealth.jsx'
import WhyHydraDB from './components/WhyHydraDB.jsx'

export default function App() {
  // 'landing' shows the product entry page; any console view key shows the console
  const [view, setView] = useState('landing')
  const [activeView, setActiveView] = useState('ask')
  const [hydraStatus, setHydraStatus] = useState({ status: 'loading', hydradb: '' })
  const [traceEntity, setTraceEntity] = useState('')

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

  const navigateToTrace = useCallback((entity) => {
    setTraceEntity(entity)
    setActiveView('trace')
    setView('console')
  }, [])

  // Entry point from landing page CTAs
  const enterConsole = useCallback((consoleView = 'ask') => {
    setActiveView(consoleView)
    setView('console')
  }, [])

  const navigateToWhyHydra = useCallback(() => {
    setActiveView('why-hydra')
    setView('console')
  }, [])

  const getBreadcrumb = () => {
    switch (activeView) {
      case 'ask': return 'INVESTIGATE / Ask'
      case 'trace': return 'INVESTIGATE / Trace'
      case 'entities': return 'EXPLORE / Entities'
      case 'why-hydra': return 'SYSTEM / Why HydraDB?'
      case 'health': return 'SYSTEM / Graph Health'
      default: return 'INVESTIGATE'
    }
  }

  if (view === 'landing') {
    return (
      <LandingPage
        onEnterConsole={enterConsole}
        onNavigateToWhyHydra={navigateToWhyHydra}
        hydraStatus={hydraStatus}
      />
    )
  }

  return (
    <div className="shell">
      <Sidebar
        activeView={activeView}
        onNavigate={(v) => { setActiveView(v); setView('console') }}
        hydraStatus={hydraStatus}
        onGoHome={() => setView('landing')}
      />
      <div className="workspace">
        <header className="workspace-header">
          <nav className="breadcrumb" aria-label="Current location">
            <button
              className="breadcrumb-home"
              onClick={() => setView('landing')}
              aria-label="Return to Veridex home"
            >
              VERIDEX
            </button>
            <span className="breadcrumb-sep">/</span>
            <span className="breadcrumb-active">{getBreadcrumb()}</span>
          </nav>
          <div className="header-status">
            <span
              className={`status-dot ${
                hydraStatus.status === 'loading' ? 'loading'
                  : hydraStatus.hydradb === 'ok' ? 'ok' : 'err'
              }`}
              aria-hidden="true"
            />
            <span>
              {hydraStatus.status === 'loading' ? 'CHECKING...'
                : hydraStatus.hydradb === 'ok' ? 'HYDRADB ONLINE' : 'HYDRADB OFFLINE'}
            </span>
          </div>
        </header>

        <main className="workspace-body" id="main-content" role="main">
          {activeView === 'ask' && <InvestigationView />}
          {activeView === 'trace' && (
            <TraceView initialEntity={traceEntity} onEntityChange={setTraceEntity} />
          )}
          {activeView === 'entities' && (
            <EntityExplorer onTraceEntity={navigateToTrace} />
          )}
          {activeView === 'why-hydra' && <WhyHydraDB />}
          {activeView === 'health' && <GraphHealth hydraStatus={hydraStatus} />}
        </main>
      </div>
    </div>
  )
}

