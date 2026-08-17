import React, { useState, useEffect, useCallback } from 'react'
import Sidebar from './components/Sidebar.jsx'
import InvestigationView from './components/InvestigationView.jsx'
import TraceView from './components/TraceView.jsx'
import EntityExplorer from './components/EntityExplorer.jsx'
import GraphHealth from './components/GraphHealth.jsx'

export default function App() {
  const [activeView, setActiveView] = useState('ask')
  const [hydraStatus, setHydraStatus] = useState({ status: 'loading', hydradb: '' })
  const [traceEntity, setTraceEntity] = useState('')

  // Periodic health check
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

  // Navigation callback from EntityExplorer -> Trace
  const navigateToTrace = useCallback((entity) => {
    setTraceEntity(entity)
    setActiveView('trace')
  }, [])

  const getBreadcrumb = () => {
    switch (activeView) {
      case 'ask':
        return 'INVESTIGATE / Ask'
      case 'trace':
        return 'INVESTIGATE / Trace'
      case 'entities':
        return 'EXPLORE / Entities'
      case 'health':
        return 'SYSTEM / Graph Health'
      default:
        return 'INVESTIGATE'
    }
  }

  return (
    <div className="shell">
      <Sidebar
        activeView={activeView}
        onNavigate={setActiveView}
        hydraStatus={hydraStatus}
      />
      <div className="workspace">
        <header className="workspace-header">
          <nav className="breadcrumb" aria-label="Current location">
            <span>VERIDEX</span>
            <span className="breadcrumb-sep">/</span>
            <span className="breadcrumb-active">{getBreadcrumb()}</span>
          </nav>
          <div className="header-status">
            <span
              className={`status-dot ${
                hydraStatus.status === 'loading'
                  ? 'loading'
                  : hydraStatus.hydradb === 'ok'
                  ? 'ok'
                  : 'err'
              }`}
              aria-hidden="true"
            />
            <span>
              {hydraStatus.status === 'loading'
                ? 'CHECKING...'
                : hydraStatus.hydradb === 'ok'
                ? 'HYDRADB ONLINE'
                : 'HYDRADB OFFLINE'}
            </span>
          </div>
        </header>

        <main className="workspace-body" id="main-content" role="main">
          {activeView === 'ask' && <InvestigationView />}
          {activeView === 'trace' && (
            <TraceView
              initialEntity={traceEntity}
              onEntityChange={setTraceEntity}
            />
          )}
          {activeView === 'entities' && (
            <EntityExplorer onTraceEntity={navigateToTrace} />
          )}
          {activeView === 'health' && (
            <GraphHealth hydraStatus={hydraStatus} />
          )}
        </main>
      </div>
    </div>
  )
}
